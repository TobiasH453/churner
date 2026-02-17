#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

if ! command -v pm2 >/dev/null 2>&1; then
  echo "ERROR: pm2 is required but not installed. Run: npm install -g pm2" >&2
  exit 1
fi

mkdir -p "${REPO_ROOT}/logs"
mkdir -p "${PM2_HOME}"
mkdir -p "${N8N_USER_FOLDER}"

echo "Starting services with PM2..."
pm2 start "${REPO_ROOT}/ecosystem.config.js" --update-env
pm2 save

echo
echo "Services started."
echo "PM2 home:          ${PM2_HOME}"
echo "PM2 app (API):     ${AMAZON_AGENT_PM2_NAME}"
echo "PM2 app (n8n):     ${N8N_PM2_NAME}"
echo "n8n user folder:   ${N8N_USER_FOLDER}"
echo "n8n UI:            http://localhost:${N8N_PORT}"
echo "Python API health: http://localhost:${SERVER_PORT}/health"
echo
pm2 status
