#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

NEXT_COMMAND="bash scripts/services-status.sh"

check_names=()
check_statuses=()
check_notes=()
fail_count=0

record_check() {
  local name="$1"
  local status="$2"
  local note="$3"
  check_names+=("${name}")
  check_statuses+=("${status}")
  check_notes+=("${note}")
  if [[ "${status}" == "FAIL" ]]; then
    fail_count=$((fail_count + 1))
  fi
}

check_file_exists() {
  local rel_path="$1"
  local label="$2"
  if [[ -f "${REPO_ROOT}/${rel_path}" ]]; then
    record_check "${label}" "PASS" "Found ${rel_path}"
  else
    record_check "${label}" "FAIL" "Missing ${rel_path}"
  fi
}

check_executable_script() {
  local rel_path="$1"
  local label="$2"
  if [[ -x "${REPO_ROOT}/${rel_path}" ]]; then
    record_check "${label}" "PASS" "Executable ${rel_path}"
  else
    record_check "${label}" "FAIL" "Script not executable: ${rel_path}"
  fi
}

run_validation_check() {
  if [[ ! -f "${REPO_ROOT}/.env" ]]; then
    record_check "Env validation" "FAIL" "Missing .env (run: cp .env.example .env)"
    return 0
  fi

  if bash "${REPO_ROOT}/scripts/validate-env.sh" >/dev/null 2>&1; then
    record_check "Env validation" "PASS" "scripts/validate-env.sh passed"
  else
    record_check "Env validation" "FAIL" "scripts/validate-env.sh failed; fix listed key names"
  fi
}

run_entrypoint_checks() {
  if bash -n "${REPO_ROOT}/scripts/services-status.sh"; then
    record_check "Service status entrypoint" "PASS" "services-status script parses"
  else
    record_check "Service status entrypoint" "FAIL" "services-status script has syntax errors"
  fi

  if bash -n "${REPO_ROOT}/scripts/audit-bundle.sh"; then
    record_check "Bundle audit entrypoint" "PASS" "audit-bundle script parses"
  else
    record_check "Bundle audit entrypoint" "FAIL" "audit-bundle script has syntax errors"
  fi
}

run_packaging_baseline_check() {
  local tmp_list
  tmp_list="$(mktemp -t installer-self-check.XXXXXX)"
  printf 'README.md\ndocs/INSTALL.md\n' >"${tmp_list}"

  if bash "${REPO_ROOT}/scripts/audit-bundle.sh" --file-list "${tmp_list}" >/dev/null 2>&1; then
    record_check "Packaging baseline" "PASS" "Bundle audit passes for safe sample list"
  else
    record_check "Packaging baseline" "FAIL" "Bundle audit failed for safe sample list"
  fi

  rm -f "${tmp_list}"
}

print_summary() {
  local idx
  echo
  echo "Installer Self-Check Summary"
  echo "============================"

  for idx in "${!check_names[@]}"; do
    printf '%-28s %-6s %s\n' "${check_names[idx]}" "${check_statuses[idx]}" "${check_notes[idx]}"
  done

  echo
  if (( fail_count > 0 )); then
    echo "RESULT: FAIL (${fail_count} blocking checks)"
    echo "NOT READY FOR SMOKE VERIFICATION"
    echo "Fix failing checks, then rerun:"
    echo "  bash scripts/installer-self-check.sh"
    return 1
  fi

  echo "RESULT: PASS"
  echo "READY FOR SMOKE VERIFICATION"
  echo "NEXT COMMAND: ${NEXT_COMMAND}"
  return 0
}

main() {
  check_file_exists "install.sh" "Installer entrypoint"
  check_file_exists ".env.example" "Template env"
  check_file_exists "docs/INSTALL.md" "Install guide"
  check_file_exists "docs/ENVIRONMENT.md" "Environment guide"
  check_file_exists "docs/PACKAGING_BASELINE.md" "Packaging baseline guide"
  check_executable_script "scripts/validate-env.sh" "Env validator"
  check_executable_script "scripts/services-status.sh" "Service status script"
  check_executable_script "scripts/audit-bundle.sh" "Bundle audit script"

  run_validation_check
  run_entrypoint_checks
  run_packaging_baseline_check

  print_summary
}

main "$@"
