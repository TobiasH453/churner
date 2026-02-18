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
  local state

  if ! state="$(
    pm2 jlist 2>/dev/null | node -e '
      const fs = require("fs");
      const procName = process.argv[1];
      const data = fs.readFileSync(0, "utf8");
      let list = [];
      try {
        list = JSON.parse(data);
      } catch (_) {
        process.exit(3);
      }
      const proc = list.find((item) => item && item.name === procName);
      if (!proc) process.exit(2);
      const status = (proc.pm2_env && proc.pm2_env.status) || "unknown";
      process.stdout.write(status);
    ' "${process_name}"
  )"; then
    print_fail "PM2 process not found: ${process_name}"
    print_remediation "Run: bash scripts/services-up.sh"
    failed=1
    return
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
  if curl -fsS --max-time 5 "${url}" >/dev/null 2>&1; then
    print_pass "${label}: ${url}"
  else
    print_fail "${label}: ${url}"
    print_remediation "Run: bash scripts/services-logs.sh all 120"
    failed=1
  fi
}

print_info "Process layer checks"
check_pm2_process "${AMAZON_AGENT_PM2_NAME}"
check_pm2_process "${N8N_PM2_NAME}"

print_info "Endpoint layer checks"
check_endpoint "API /health" "http://localhost:${SERVER_PORT}/health"
check_endpoint "n8n /healthz" "http://localhost:${N8N_PORT}/healthz"

if [[ "${failed}" -ne 0 ]]; then
  print_fail "Runtime status check failed."
  print_remediation "Run: bash scripts/services-up.sh"
  exit 1
fi

print_pass "Runtime status check passed."
