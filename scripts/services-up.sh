#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

usage() {
  cat <<'EOF'
Usage: bash scripts/services-up.sh

Starts API and n8n services using PM2 ecosystem config.
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command "pm2" "npm install -g pm2" || exit 1

mkdir -p "${REPO_ROOT}/logs" "${PM2_HOME}" "${N8N_USER_FOLDER}"

print_info "Starting services from ${REPO_ROOT}/ecosystem.config.js"
if pm2 start "${REPO_ROOT}/ecosystem.config.js" --update-env >/dev/null; then
  pm2 save >/dev/null
  print_pass "Services started and PM2 state saved."
else
  print_fail "PM2 failed to start one or more services."
  print_remediation "Run: source scripts/service-env.sh && pm2 logs --lines 100"
  exit 1
fi

print_info "PM2 home: ${PM2_HOME}"
print_info "API app: ${AMAZON_AGENT_PM2_NAME}"
print_info "n8n app: ${N8N_PM2_NAME}"
print_info "API health: http://localhost:${SERVER_PORT}/health"
print_info "n8n health: http://localhost:${N8N_PORT}/healthz"
print_info "Next: bash scripts/services-status.sh"
