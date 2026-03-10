#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

if ! declare -F install_info >/dev/null 2>&1; then
  install_info() { printf '[INFO] %s\n' "$1"; }
  install_ok() { printf '[PASS] %s\n' "$1"; }
  install_warn() { printf '[WARN] %s\n' "$1"; }
  install_error() { printf '[FAIL] %s\n' "$1"; }
fi

PREFLIGHT_TIMEOUT_SECONDS="${PREFLIGHT_TIMEOUT_SECONDS:-8}"
PREFLIGHT_ERRORS=()
PREFLIGHT_FIX_COMMANDS=()
PREFLIGHT_FIX_DIRECTORIES=()
PREFLIGHT_FIX_REASONS=()

record_failure() {
  local failure="$1"
  local command="$2"
  local directory="$3"
  local reason="$4"
  PREFLIGHT_ERRORS+=("${failure}")
  PREFLIGHT_FIX_COMMANDS+=("${command}")
  PREFLIGHT_FIX_DIRECTORIES+=("${directory}")
  PREFLIGHT_FIX_REASONS+=("${reason}")
}

check_command() {
  local cmd="$1"
  local install_command="$2"
  local reason="$3"
  if command -v "${cmd}" >/dev/null 2>&1; then
    install_ok "Found dependency: ${cmd}"
  else
    record_failure \
      "Missing required dependency: ${cmd}" \
      "${install_command}" \
      "${REPO_ROOT}" \
      "${reason}"
  fi
}

check_network_probe() {
  local label="$1"
  local url="$2"
  if curl -fsSIL --max-time "${PREFLIGHT_TIMEOUT_SECONDS}" "${url}" >/dev/null 2>&1; then
    install_ok "Network probe ok: ${label}"
  else
    record_failure \
      "Network check failed: ${label} (${url})" \
      "curl -I ${url}" \
      "${REPO_ROOT}" \
      "Network checks are hard failures because dependency installs require internet access."
  fi
}

check_partial_state() {
  local env_dir
  for env_dir in venv venv314 venv313 venv312 venv39; do
    if [[ -d "${REPO_ROOT}/${env_dir}" && ! -x "${REPO_ROOT}/${env_dir}/bin/python3" ]]; then
      record_failure \
        "Detected partial setup: ${env_dir} exists but python binary is missing." \
        "rm -rf ${env_dir} && bash scripts/rebuild_venv.sh ${env_dir}" \
        "${REPO_ROOT}" \
        "Incomplete virtual environment can produce non-deterministic install behavior."
    fi
  done

  if [[ -f "${REPO_ROOT}/.env" && ! -s "${REPO_ROOT}/.env" ]]; then
    record_failure \
      "Detected partial setup: .env exists but is empty." \
      "cp .env.example .env && bash scripts/validate-env.sh" \
      "${REPO_ROOT}" \
      "Installer requires a populated .env before service startup."
  fi
}

render_failure_summary() {
  local idx
  install_error "Preflight failed with ${#PREFLIGHT_ERRORS[@]} blocking issue(s):"
  for idx in "${!PREFLIGHT_ERRORS[@]}"; do
    printf '  %d) %s\n' "$((idx + 1))" "${PREFLIGHT_ERRORS[idx]}"
  done

  echo
  install_warn "Manual remediation steps:"
  for idx in "${!PREFLIGHT_FIX_COMMANDS[@]}"; do
    printf '  %d) Command: %s\n' "$((idx + 1))" "${PREFLIGHT_FIX_COMMANDS[idx]}"
    printf '     Directory: %s\n' "${PREFLIGHT_FIX_DIRECTORIES[idx]}"
    printf '     Reason: %s\n' "${PREFLIGHT_FIX_REASONS[idx]}"
  done
}

run_preflight() {
  PREFLIGHT_ERRORS=()
  PREFLIGHT_FIX_COMMANDS=()
  PREFLIGHT_FIX_DIRECTORIES=()
  PREFLIGHT_FIX_REASONS=()

  install_info "Running deterministic preflight checks..."

  check_command "bash" "brew install bash" "Installer requires a modern Bash runtime."
  check_command "python3" "brew install python@3.13" "Python 3.13 is the preferred runtime for FastAPI and browser automation."
  check_command "pip3" "python3 -m ensurepip --upgrade" "pip is required to install Python dependencies."
  check_command "node" "brew install node" "Node.js powers n8n and JS tooling."
  check_command "npm" "brew install node" "npm is required for global n8n/pm2 install."
  check_command "pm2" "npm install -g pm2" "PM2 manages local API and n8n services."
  check_command "n8n" "npm install -g n8n" "n8n runtime is required for workflow execution."
  check_command "curl" "brew install curl" "curl is required for health checks and probes."
  check_command "git" "xcode-select --install" "git is required to manage and package repository artifacts."
  check_command "tar" "xcode-select --install" "tar is required for packaging audit operations."

  check_network_probe "PyPI" "https://pypi.org/simple/"
  check_network_probe "NPM Registry" "https://registry.npmjs.org/"
  check_network_probe "GitHub API" "https://api.github.com/"

  check_partial_state

  if [[ ${#PREFLIGHT_ERRORS[@]} -gt 0 ]]; then
    render_failure_summary
    return 1
  fi

  install_ok "Preflight completed with no blocking issues."
  return 0
}
