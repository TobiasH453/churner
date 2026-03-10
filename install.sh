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
  local env_validation_state="SKIPPED"
  local next_command="bash install.sh"

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
      set +e
      bash "${ROOT_DIR}/scripts/validate-env.sh" --allow-template-placeholders
      env_validation_rc=$?
      set -e

      case "${env_validation_rc}" in
        0)
          install_ok "Environment validation passed."
          env_validation_ok=1
          env_validation_state="PASS"
          next_command="bash scripts/services-up.sh"
          ;;
        20)
          install_warn "Environment validation is pending because .env still contains shipped placeholder values."
          install_info "Edit .env locally, then rerun: bash scripts/validate-env.sh"
          ;;
        *)
          install_error "Environment validation failed. Fix .env and rerun bash scripts/validate-env.sh before starting services."
          env_validation_state="FAIL"
          ;;
      esac
    else
      install_warn "scripts/validate-env.sh is not present yet."
    fi

    bootstrap_ok=1
  fi

  install_print_header "Summary"
  install_summary_line "Preflight" "$( [[ ${preflight_ok} -eq 1 ]] && echo 'PASS' || echo 'FAIL' )"
  install_summary_line "Bootstrap" "$( [[ ${bootstrap_ok} -eq 1 ]] && echo 'PASS' || echo 'SKIPPED' )"
  install_summary_line "Env Validation" "${env_validation_state}"
  install_summary_line "Install Log" "${INSTALL_LOG_FILE}"

  echo
  echo "Done:"
  echo "  1) Deterministic preflight checks"
  if [[ ${bootstrap_ok} -eq 1 ]]; then
    echo "  2) Local setup scaffolding"
  fi
  echo
  echo "Remaining:"
  if [[ ${preflight_ok} -eq 0 ]]; then
    echo "  1) Resolve preflight blockers and rerun bash install.sh"
  elif [[ "${env_validation_state}" == "PASS" ]]; then
    echo "  1) Start services"
  else
    echo "  1) Edit .env locally and rerun bash scripts/validate-env.sh"
    echo "  2) Start services after env validation passes"
  fi
  echo
  echo "Next command:"
  echo "  ${next_command}"

  if [[ ${INSTALL_FAILED} -eq 1 ]]; then
    exit 1
  fi
}

main "$@"
