#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
SERVICE_SCRIPTS_DIR="${SERVICE_SCRIPTS_DIR:-${REPO_ROOT}/scripts}"

usage() {
  cat <<'USAGE'
Usage: bash scripts/verify-runtime-operations.sh

Runs runtime validation in this exact order:
1) services-up
2) services-status
3) services-logs (bounded)
4) services-down

Returns non-zero on first blocking failure.
USAGE
}

print_info() {
  printf '[INFO] %s\n' "$1"
}

print_pass() {
  printf '[PASS] %s\n' "$1"
}

print_fail() {
  printf '[FAIL] %s\n' "$1" >&2
}

print_next() {
  printf '       Next: %s\n' "$1" >&2
}

run_stage() {
  local stage_name="$1"
  local remediation="$2"
  shift 2

  print_info "Stage: ${stage_name}"
  if "$@"; then
    print_pass "${stage_name}"
    return 0
  else
    local exit_code=$?
    print_fail "${stage_name}"
    print_next "${remediation}"
    return "${exit_code}"
  fi
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -x "${SERVICE_SCRIPTS_DIR}/services-up.sh" ]]; then
  print_fail "Missing executable: ${SERVICE_SCRIPTS_DIR}/services-up.sh"
  print_next "Ensure runtime service scripts are present, then rerun."
  exit 1
fi

cleanup_needed=0
cleanup() {
  if [[ "${cleanup_needed}" -eq 1 ]]; then
    print_info "Cleanup: stopping services after failure"
    bash "${SERVICE_SCRIPTS_DIR}/services-down.sh" >/dev/null 2>&1 || true
  fi
}
trap cleanup EXIT

run_stage \
  "Start services (services-up)" \
  "bash scripts/services-up.sh" \
  bash "${SERVICE_SCRIPTS_DIR}/services-up.sh" || exit $?
cleanup_needed=1

run_stage \
  "Check runtime health (services-status)" \
  "bash scripts/services-logs.sh all 120" \
  bash "${SERVICE_SCRIPTS_DIR}/services-status.sh" || exit $?

run_stage \
  "Retrieve bounded logs (services-logs)" \
  "bash scripts/services-logs.sh all 120" \
  bash "${SERVICE_SCRIPTS_DIR}/services-logs.sh" all 80 || exit $?

run_stage \
  "Stop services (services-down)" \
  "bash scripts/services-down.sh" \
  bash "${SERVICE_SCRIPTS_DIR}/services-down.sh" || exit $?
cleanup_needed=0

print_pass "Runtime operations validation passed."
print_info "Next: Review docs/RUNTIME_VALIDATION.md for interpretation guidance."
