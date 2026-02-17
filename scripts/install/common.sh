#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

INSTALL_LOG_DIR="${INSTALL_LOG_DIR:-${REPO_ROOT}/logs/install}"
INSTALL_LOG_FILE="${INSTALL_LOG_FILE:-${INSTALL_LOG_DIR}/install-$(date -u +%Y%m%dT%H%M%SZ).log}"
INSTALL_FAILED=0

install_init_logging() {
  mkdir -p "${INSTALL_LOG_DIR}"
  exec > >(tee -a "${INSTALL_LOG_FILE}") 2>&1
}

install_print_header() {
  local title="$1"
  echo
  printf '========== %s ==========%s' "${title}" "\n"
}

install_info() {
  printf '[INFO] %s\n' "$1"
}

install_ok() {
  printf '[PASS] %s\n' "$1"
}

install_warn() {
  printf '[WARN] %s\n' "$1"
}

install_error() {
  printf '[FAIL] %s\n' "$1"
  INSTALL_FAILED=1
}

install_manual_step() {
  local command="$1"
  local working_dir="$2"
  local reason="$3"

  echo
  install_warn "Manual step required"
  echo "  Command: ${command}"
  echo "  Directory: ${working_dir}"
  echo "  Reason: ${reason}"

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
  printf '  - %-24s %s\n' "${label}" "${status}"
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
