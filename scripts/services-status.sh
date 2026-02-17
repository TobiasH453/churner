#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

if ! command -v pm2 >/dev/null 2>&1; then
  echo "ERROR: pm2 is required but not installed. Run: npm install -g pm2" >&2
  exit 1
fi

echo "PM2 process status:"
pm2 status
echo

echo "FastAPI health check:"
HEALTH_FILE="$(mktemp -t amazon-agent-health.XXXXXX.json)"
if curl -fsS "http://localhost:${SERVER_PORT}/health" >"${HEALTH_FILE}" 2>/dev/null; then
  cat "${HEALTH_FILE}"
  echo
else
  echo "FAILED: http://localhost:${SERVER_PORT}/health"
fi
rm -f "${HEALTH_FILE}"

echo
echo "n8n health check:"
if curl -fsS "http://localhost:${N8N_PORT}" >/dev/null 2>&1; then
  echo "OK: http://localhost:${N8N_PORT}"
else
  echo "FAILED: http://localhost:${N8N_PORT}"
fi
