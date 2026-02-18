#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

usage() {
  cat <<'EOF'
Usage: bash scripts/services-status.sh

Reports PM2 process state and API/n8n endpoint health.
Returns non-zero if any blocking check fails.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command "pm2" "npm install -g pm2" || exit 1
require_command "curl" "Install curl and rerun." || exit 1

failed=0

check_pm2_process() {
  local process_name="$1"
  local state=""
  local describe_output

  if ! describe_output="$(pm2 describe "${process_name}" 2>/dev/null)"; then
    print_fail "PM2 process not found: ${process_name}"
    print_remediation "Run: bash scripts/services-up.sh"
    failed=1
    return
  fi

  state="$(printf '%s\n' "${describe_output}" | sed -nE 's/.*status[[:space:]]*[|│][[:space:]]*([a-zA-Z_-]+).*/\1/p' | head -1)"
  if [[ -z "${state}" ]]; then
    state="unknown"
  fi

  if [[ "${state}" == "online" ]]; then
    print_pass "PM2 ${process_name}: online"
  else
    print_fail "PM2 ${process_name}: ${state}"
    print_remediation "Run: bash scripts/services-logs.sh ${process_name} 120"
    failed=1
  fi
}

check_endpoint() {
  local label="$1"
  local url="$2"
  local remediation_target="$3"
  if curl -fsS --max-time 5 "${url}" >/dev/null 2>&1; then
    print_pass "${label}: ${url}"
  else
    print_fail "${label}: ${url}"
    print_remediation "Run: bash scripts/services-logs.sh ${remediation_target} 120"
    failed=1
  fi
}

print_info "Process layer checks"
check_pm2_process "${AMAZON_AGENT_PM2_NAME}"
check_pm2_process "${N8N_PM2_NAME}"

print_info "Endpoint layer checks"
check_endpoint "API /health" "http://localhost:${SERVER_PORT}/health" "amazon-agent"
check_endpoint "n8n /healthz" "http://localhost:${N8N_PORT}/healthz" "n8n-server"

if [[ "${failed}" -ne 0 ]]; then
  print_fail "Runtime status check failed."
  print_remediation "Run: bash scripts/services-up.sh"
  exit 1
fi

print_pass "Runtime status check passed."
