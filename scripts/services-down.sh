#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

usage() {
  cat <<'EOF'
Usage: bash scripts/services-down.sh

Stops API and n8n services managed by PM2.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command "pm2" "npm install -g pm2" || exit 1

print_info "Stopping PM2 services..."

missing=0
if pm2 describe "${AMAZON_AGENT_PM2_NAME}" >/dev/null 2>&1; then
  pm2 delete "${AMAZON_AGENT_PM2_NAME}" >/dev/null
  print_pass "Stopped ${AMAZON_AGENT_PM2_NAME}"
else
  missing=1
  print_warn "${AMAZON_AGENT_PM2_NAME} is not currently registered in PM2."
fi

if pm2 describe "${N8N_PM2_NAME}" >/dev/null 2>&1; then
  pm2 delete "${N8N_PM2_NAME}" >/dev/null
  print_pass "Stopped ${N8N_PM2_NAME}"
else
  missing=1
  print_warn "${N8N_PM2_NAME} is not currently registered in PM2."
fi

pm2 save >/dev/null
if [[ "${missing}" -eq 1 ]]; then
  print_warn "One or more services were already stopped."
else
  print_pass "All services stopped and PM2 state saved."
fi
print_info "Next: bash scripts/services-status.sh"
