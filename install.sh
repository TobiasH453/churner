#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${ROOT_DIR}/scripts/install/common.sh"
source "${ROOT_DIR}/scripts/install/preflight.sh"

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  install_usage
  exit 0
fi

main() {
  local preflight_ok=0
  local bootstrap_ok=0
  local env_validation_ok=0

  install_init_logging

  install_print_header "Preflight"
  if run_preflight; then
    install_ok "Preflight checks passed."
    preflight_ok=1
  else
    install_error "Preflight checks failed. Resolve blockers and rerun install.sh."
  fi

  if [[ ${preflight_ok} -eq 1 ]]; then
    install_print_header "Bootstrap"

    mkdir -p "${ROOT_DIR}/logs" "${ROOT_DIR}/data"

    if [[ ! -f "${ROOT_DIR}/.env" ]]; then
      if [[ -f "${ROOT_DIR}/.env.example" ]]; then
        cp "${ROOT_DIR}/.env.example" "${ROOT_DIR}/.env"
        install_ok "Created .env from .env.example"
      else
        install_warn ".env.example not found yet. Create it before runtime startup."
      fi
    fi

    if [[ -f "${ROOT_DIR}/scripts/validate-env.sh" ]]; then
      if bash "${ROOT_DIR}/scripts/validate-env.sh"; then
        install_ok "Environment validation passed."
        env_validation_ok=1
      else
        install_error "Environment validation failed."
      fi
    else
      install_warn "scripts/validate-env.sh is not present yet."
    fi

    install_manual_step \
      "source venv314/bin/activate" \
      "${ROOT_DIR}" \
      "Activate project virtualenv before running manual automation checks."

    bootstrap_ok=1
  fi

  install_print_header "Summary"
  install_summary_line "Preflight" "$( [[ ${preflight_ok} -eq 1 ]] && echo 'PASS' || echo 'FAIL' )"
  install_summary_line "Bootstrap" "$( [[ ${bootstrap_ok} -eq 1 ]] && echo 'PASS' || echo 'SKIPPED' )"
  install_summary_line "Env Validation" "$( [[ ${env_validation_ok} -eq 1 ]] && echo 'PASS' || echo 'PENDING' )"
  install_summary_line "Install Log" "${INSTALL_LOG_FILE}"

  echo
  echo "Done:"
  echo "  1) Deterministic preflight checks"
  echo "  2) Local setup scaffolding"
  echo
  echo "Remaining:"
  echo "  1) Confirm .env values are filled"
  echo "  2) Start services"
  echo
  echo "Next command:"
  echo "  bash scripts/services-up.sh"

  if [[ ${INSTALL_FAILED} -eq 1 ]]; then
    exit 1
  fi
}

main "$@"
