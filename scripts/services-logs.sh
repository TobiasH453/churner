#!/usr/bin/env bash
set -euo pipefail

TARGET="${1:-all}"
LINES="${2:-100}"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

if ! command -v pm2 >/dev/null 2>&1; then
  echo "ERROR: pm2 is required but not installed. Run: npm install -g pm2" >&2
  exit 1
fi

case "${TARGET}" in
  all)
    echo "Streaming logs for all services (last ${LINES} lines)..."
    pm2 logs --lines "${LINES}"
    ;;
  amazon-agent|agent)
    echo "Streaming logs for ${AMAZON_AGENT_PM2_NAME} (last ${LINES} lines)..."
    pm2 logs "${AMAZON_AGENT_PM2_NAME}" --lines "${LINES}"
    ;;
  n8n-server|n8n)
    echo "Streaming logs for ${N8N_PM2_NAME} (last ${LINES} lines)..."
    pm2 logs "${N8N_PM2_NAME}" --lines "${LINES}"
    ;;
  *)
    echo "Usage: $0 [all|amazon-agent|agent|n8n-server|n8n] [lines]"
    exit 1
    ;;
esac
