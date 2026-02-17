#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

if ! command -v pm2 >/dev/null 2>&1; then
  echo "ERROR: pm2 is required but not installed. Run: npm install -g pm2" >&2
  exit 1
fi

echo "Stopping PM2 services..."
pm2 delete "${AMAZON_AGENT_PM2_NAME}" || true
pm2 delete "${N8N_PM2_NAME}" || true
pm2 save

echo
echo "Services stopped."
pm2 status
