#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

INSTALL_LOG_DIR="${INSTALL_LOG_DIR:-${REPO_ROOT}/logs/install}"
INSTALL_LOG_FILE="${INSTALL_LOG_FILE:-${INSTALL_LOG_DIR}/install-$(date -u +%Y%m%dT%H%M%SZ).log}"
INSTALL_FAILED=0

install_init_logging() {
  mkdir -p "${INSTALL_LOG_DIR}"
  : >"${INSTALL_LOG_FILE}"
}

install_emit() {
  local message="$1"
  printf '%s\n' "${message}"
  printf '%s\n' "${message}" >>"${INSTALL_LOG_FILE}"
}

install_print_header() {
  local title="$1"
  install_emit ""
  install_emit "========== ${title} =========="
}

install_info() {
  install_emit "[INFO] $1"
}

install_ok() {
  install_emit "[PASS] $1"
}

install_warn() {
  install_emit "[WARN] $1"
}

install_error() {
  install_emit "[FAIL] $1"
  INSTALL_FAILED=1
}

install_manual_step() {
  local command="$1"
  local working_dir="$2"
  local reason="$3"

  install_emit ""
  install_warn "Manual step required"
  install_emit "  Command: ${command}"
  install_emit "  Directory: ${working_dir}"
  install_emit "  Reason: ${reason}"

  if [[ -t 0 ]]; then
    printf 'Press Enter after completing this step to continue... '
    read -r _
  else
    install_error "Manual step requires an interactive terminal."
    return 1
  fi
}

install_summary_line() {
  local label="$1"
  local status="$2"
  local line
  line="$(printf '  - %-24s %s' "${label}" "${status}")"
  install_emit "${line}"
}

install_usage() {
  cat <<USAGE
Usage: bash install.sh

Runs deterministic setup in three sections:
1) preflight checks
2) bootstrap actions
3) final summary
USAGE
}
