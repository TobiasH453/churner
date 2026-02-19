#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

SMOKE_HEALTH_URL="${SMOKE_HEALTH_URL:-http://localhost:${SERVER_PORT}/health}"

usage() {
  cat <<'EOF'
Usage: bash scripts/verify-smoke-readiness.sh

Runs the Phase 4 smoke readiness baseline:
1) API health endpoint check

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

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command "curl" "Install curl and rerun: bash scripts/verify-smoke-readiness.sh" || exit 1

run_stage \
  "Check API health endpoint" \
  "Run: bash scripts/services-status.sh" \
  check_health || exit $?

print_warn "Order and shipping contract checks are added in Phase 4 plans 04-02 and 04-03."
print_pass "Smoke readiness baseline passed."
print_info "Next: bash scripts/services-status.sh"
