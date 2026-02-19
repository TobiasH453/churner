#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

SMOKE_HEALTH_TIMEOUT="${SMOKE_HEALTH_TIMEOUT:-${SMOKE_REQUEST_TIMEOUT}}"
SMOKE_HEALTH_URL="${SMOKE_HEALTH_URL:-http://localhost:${SERVER_PORT}/health}"
SMOKE_API_URL="${SMOKE_API_URL:-http://localhost:${SERVER_PORT}/process-order}"
SMOKE_ORDER_NUMBER="${SMOKE_ORDER_NUMBER:-}"
SMOKE_ORDER_ACCOUNT_TYPE="${SMOKE_ORDER_ACCOUNT_TYPE:-amz_personal}"
if [[ -x "${PYTHON_BIN}" ]]; then
  SMOKE_PYTHON_BIN="${SMOKE_PYTHON_BIN:-${PYTHON_BIN}}"
else
  SMOKE_PYTHON_BIN="${SMOKE_PYTHON_BIN:-python3}"
fi

usage() {
  cat <<'EOF'
Usage: bash scripts/verify-smoke-readiness.sh

Runs the Phase 4 smoke readiness checks:
1) API health endpoint check
2) Order-confirmation contract check
3) Shipping-confirmation contract check

Returns non-zero on blocking failures.
EOF
}

run_stage() {
  local stage_name="$1"
  local remediation="$2"
  shift 2

  print_info "Stage: ${stage_name}"
  if "$@"; then
    print_pass "${stage_name}"
    return 0
  fi

  print_fail "${stage_name}"
  print_remediation "${remediation}"
  return 1
}

check_health() {
  local response
  if ! response="$(curl --silent --show-error \
    --fail-with-body \
    --connect-timeout "${SMOKE_CONNECT_TIMEOUT}" \
    --max-time "${SMOKE_HEALTH_TIMEOUT}" \
    "${SMOKE_HEALTH_URL}")"; then
    print_fail "API /health check failed: ${SMOKE_HEALTH_URL}"
    return 1
  fi

  if ! printf '%s' "${response}" | grep -q '"status"'; then
    print_fail "API /health response missing status field."
    return 1
  fi

  print_info "Health response: ${response}"
  return 0
}

check_order_contract() {
  local payload response

  if [[ -z "${SMOKE_ORDER_NUMBER}" ]]; then
    print_fail "Missing smoke input: SMOKE_ORDER_NUMBER"
    return 1
  fi

  payload="$(printf '{"email_type":"order_confirmation","order_number":"%s","account_type":"%s"}' \
    "${SMOKE_ORDER_NUMBER}" "${SMOKE_ORDER_ACCOUNT_TYPE}")"

  if ! response="$(curl --silent --show-error \
    --fail-with-body \
    --connect-timeout "${SMOKE_CONNECT_TIMEOUT}" \
    --max-time "${SMOKE_REQUEST_TIMEOUT}" \
    -H 'Content-Type: application/json' \
    --data "${payload}" \
    "${SMOKE_API_URL}")"; then
    print_fail "Order smoke request failed: ${SMOKE_API_URL}"
    return 1
  fi

  if ! printf '%s' "${response}" | "${SMOKE_PYTHON_BIN}" "${SCRIPT_DIR}/smoke-validate-response.py" \
    --expected-email-type order_confirmation; then
    print_fail "Order smoke response failed contract validation."
    return 1
  fi

  print_info "Order response contract validated."
  return 0
}

check_shipping_contract() {
  local payload response shipping_order

  shipping_order="${SMOKE_SHIPPING_ORDER_NUMBER:-${SMOKE_ORDER_NUMBER}}"
  if [[ -z "${shipping_order}" ]]; then
    print_fail "Missing smoke input: SMOKE_SHIPPING_ORDER_NUMBER (or SMOKE_ORDER_NUMBER fallback)"
    return 1
  fi

  payload="$(printf '{"email_type":"shipping_confirmation","order_number":"%s","account_type":"%s"}' \
    "${shipping_order}" "${SMOKE_ORDER_ACCOUNT_TYPE}")"

  if ! response="$(curl --silent --show-error \
    --fail-with-body \
    --connect-timeout "${SMOKE_CONNECT_TIMEOUT}" \
    --max-time "${SMOKE_REQUEST_TIMEOUT}" \
    -H 'Content-Type: application/json' \
    --data "${payload}" \
    "${SMOKE_API_URL}")"; then
    print_fail "Shipping smoke request failed: ${SMOKE_API_URL}"
    return 1
  fi

  if ! printf '%s' "${response}" | "${SMOKE_PYTHON_BIN}" "${SCRIPT_DIR}/smoke-validate-response.py" \
    --expected-email-type shipping_confirmation; then
    print_fail "Shipping smoke response failed contract validation."
    return 1
  fi

  print_info "Shipping response contract validated."
  return 0
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command "curl" "Install curl and rerun: bash scripts/verify-smoke-readiness.sh" || exit 1
if [[ "${SMOKE_PYTHON_BIN}" == */* ]]; then
  if [[ ! -x "${SMOKE_PYTHON_BIN}" ]]; then
    print_fail "Missing dependency: ${SMOKE_PYTHON_BIN}"
    print_remediation "Create project virtualenv or set SMOKE_PYTHON_BIN=python3 before rerunning."
    exit 1
  fi
else
  require_command "${SMOKE_PYTHON_BIN}" "Install Python 3 and rerun: bash scripts/verify-smoke-readiness.sh" || exit 1
fi

print_info "Stage order: health -> order -> shipping"
run_stage \
  "Check API health endpoint" \
  "Run: bash scripts/services-status.sh" \
  check_health || exit $?

order_failed=0
shipping_failed=0

run_stage \
  "Check order-confirmation contract path" \
  "Export SMOKE_ORDER_NUMBER and rerun: SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh" \
  check_order_contract || order_failed=1

run_stage \
  "Check shipping-confirmation contract path" \
  "Export SMOKE_SHIPPING_ORDER_NUMBER (or SMOKE_ORDER_NUMBER) and rerun: SMOKE_SHIPPING_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh" \
  check_shipping_contract || shipping_failed=1

if [[ "${order_failed}" -ne 0 || "${shipping_failed}" -ne 0 ]]; then
  print_fail "Smoke readiness checks failed."
  print_remediation "Run: bash scripts/services-logs.sh amazon-agent 120"
  print_remediation "Review: docs/SMOKE_VERIFICATION.md"
  exit 1
fi

print_pass "Smoke readiness checks passed: health + order + shipping."
print_info "Next: use docs/SMOKE_VERIFICATION.md for rerun scenarios and troubleshooting."
