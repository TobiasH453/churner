#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

usage() {
  cat <<'EOF'
Usage: bash scripts/services-logs.sh [all|amazon-agent|agent|n8n-server|n8n] [lines] [--follow]

Defaults:
- target: all
- lines: 100
- mode: snapshot (non-streaming)
EOF
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

require_command "pm2" "npm install -g pm2" || exit 1

TARGET="${1:-all}"
LINES="${2:-100}"
FOLLOW="${3:-}"

if ! is_positive_integer "${LINES}"; then
  print_fail "Line count must be a positive integer. Received: ${LINES}"
  print_remediation "Run: bash scripts/services-logs.sh all 100"
  exit 1
fi

stream_flag="--nostream"
if [[ "${FOLLOW}" == "--follow" ]]; then
  stream_flag=""
fi

case "${TARGET}" in
  all)
    print_info "Logs target=all lines=${LINES} mode=${FOLLOW:---snapshot}"
    pm2 logs --lines "${LINES}" ${stream_flag}
    ;;
  amazon-agent|agent)
    print_info "Logs target=${AMAZON_AGENT_PM2_NAME} lines=${LINES} mode=${FOLLOW:---snapshot}"
    pm2 logs "${AMAZON_AGENT_PM2_NAME}" --lines "${LINES}" ${stream_flag}
    ;;
  n8n-server|n8n)
    print_info "Logs target=${N8N_PM2_NAME} lines=${LINES} mode=${FOLLOW:---snapshot}"
    pm2 logs "${N8N_PM2_NAME}" --lines "${LINES}" ${stream_flag}
    ;;
  *)
    print_fail "Unknown target: ${TARGET}"
    usage
    exit 1
    ;;
esac

print_pass "Log command completed."
