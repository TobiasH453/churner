#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

slugify() {
  local raw="$1"
  local slug
  slug="$(echo "${raw}" | tr '[:upper:]' '[:lower:]' | sed -E 's/[^a-z0-9]+/-/g; s/^-+//; s/-+$//')"
  if [[ -z "${slug}" ]]; then
    slug="repo"
  fi
  echo "${slug}"
}

REPO_SLUG="$(slugify "$(basename "${REPO_ROOT}")")"

export REPO_ROOT
export REPO_SLUG
export PM2_HOME="${PM2_HOME:-${REPO_ROOT}/.pm2}"
export AMAZON_AGENT_PM2_NAME="${AMAZON_AGENT_PM2_NAME:-amazon-agent-${REPO_SLUG}}"
export N8N_PM2_NAME="${N8N_PM2_NAME:-n8n-server-${REPO_SLUG}}"
export SERVER_PORT="${SERVER_PORT:-18080}"
export N8N_PORT="${N8N_PORT:-15678}"
export N8N_USER_FOLDER="${N8N_USER_FOLDER:-${REPO_ROOT}/.n8n}"
export PYTHON_BIN="${PYTHON_BIN:-${REPO_ROOT}/venv314/bin/python}"
export N8N_BIN="${N8N_BIN:-/usr/local/bin/n8n}"
