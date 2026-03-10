#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/verify-release-readiness.sh [--archive /path/to/release.zip]

Checks that release-facing docs, scripts, and command references are present and aligned.
If --archive is provided, also runs the bundle audit against that archive.
USAGE
}

failures=0
archive_path=""
RELEASE_TRACKED_FILES=()

record_failure() {
  local message="$1"
  print_fail "${message}"
  failures=1
}

require_file() {
  local rel_path="$1"
  if [[ ! -e "${REPO_ROOT}/${rel_path}" ]]; then
    record_failure "Missing required file: ${rel_path}"
  else
    print_pass "Found required file: ${rel_path}"
  fi
}

require_executable() {
  local rel_path="$1"
  if [[ ! -x "${REPO_ROOT}/${rel_path}" ]]; then
    record_failure "Missing executable bit: ${rel_path}"
  else
    print_pass "Executable ok: ${rel_path}"
  fi
}

require_committed_path() {
  local rel_path="$1"
  if git -C "${REPO_ROOT}" cat-file -e "HEAD:${rel_path}" 2>/dev/null; then
    print_pass "Committed at HEAD: ${rel_path}"
  else
    record_failure "Required release input is not committed at HEAD: ${rel_path}"
  fi
}

collect_committed_dir_files() {
  local dir_path="$1"
  local tracked_files=()
  local tracked_file

  if [[ ! -d "${REPO_ROOT}/${dir_path}" ]]; then
    record_failure "Missing required directory: ${dir_path}"
    return 0
  fi

  if ! git -C "${REPO_ROOT}" cat-file -e "HEAD:${dir_path}" 2>/dev/null; then
    record_failure "Required release directory is not committed at HEAD: ${dir_path}"
    return 0
  fi

  while IFS= read -r tracked_file; do
    tracked_files+=("${tracked_file}")
  done < <(git -C "${REPO_ROOT}" ls-tree -r --name-only HEAD -- "${dir_path}")
  if (( ${#tracked_files[@]} == 0 )); then
    record_failure "Required release directory has no committed contents at HEAD: ${dir_path}"
    return 0
  fi

  RELEASE_TRACKED_FILES+=("${tracked_files[@]}")
  print_pass "Committed release directory contents found: ${dir_path}"
}

report_release_input_drift() {
  if (( ${#RELEASE_TRACKED_FILES[@]} == 0 )); then
    record_failure "Release tracked input list is empty."
    return 0
  fi

  if git -C "${REPO_ROOT}" diff --quiet -- "${RELEASE_TRACKED_FILES[@]}"; then
    print_pass "Required release inputs match committed HEAD in the working tree."
  else
    print_warn "Required release inputs have working-tree drift; release build will package committed HEAD versions instead."
  fi

  if git -C "${REPO_ROOT}" diff --cached --quiet -- "${RELEASE_TRACKED_FILES[@]}"; then
    print_pass "Required release inputs have no staged-only drift."
  else
    print_warn "Required release inputs have staged-only drift; release build will package committed HEAD versions instead."
  fi
}

assert_contains() {
  local rel_path="$1"
  local needle="$2"
  if rg -Fq "${needle}" "${REPO_ROOT}/${rel_path}"; then
    print_pass "${rel_path} contains: ${needle}"
  else
    record_failure "${rel_path} is missing expected text: ${needle}"
  fi
}

assert_before() {
  local rel_path="$1"
  local first="$2"
  local second="$3"
  local first_line
  local second_line

  first_line="$(rg -n -F "${first}" "${REPO_ROOT}/${rel_path}" | head -n 1 | cut -d: -f1 || true)"
  second_line="$(rg -n -F "${second}" "${REPO_ROOT}/${rel_path}" | head -n 1 | cut -d: -f1 || true)"

  if [[ -z "${first_line}" || -z "${second_line}" ]]; then
    record_failure "${rel_path} is missing ordering anchors: ${first} | ${second}"
    return 0
  fi

  if (( first_line < second_line )); then
    print_pass "${rel_path} order ok: ${first} before ${second}"
  else
    record_failure "${rel_path} has incorrect order: expected ${first} before ${second}"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --archive)
      archive_path="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      record_failure "Unknown argument: $1"
      print_remediation "Run bash scripts/verify-release-readiness.sh --help"
      exit 1
      ;;
  esac
done

require_command "git" "Install git and rerun bash scripts/verify-release-readiness.sh" || exit 1

print_info "Checking required release artifacts"
for rel_path in \
  README.md \
  docs/RELEASE.md \
  docs/RELEASE_CHECKLIST.md \
  docs/N8N_INTEGRATION.md \
  docs/TROUBLESHOOTING.md \
  scripts/build-release-bundle.sh \
  scripts/verify-release-readiness.sh \
  scripts/audit-bundle.sh \
  scripts/validate-env.sh \
  scripts/services-up.sh \
  scripts/services-status.sh \
  scripts/verify-runtime-operations.sh \
  scripts/verify-n8n-workflow-contract.sh \
  scripts/verify-smoke-readiness.sh \
  scripts/collect-diagnostics.sh \
  install.sh \
  n8n-workflows/03-process-order-v1.0.0.json; do
  require_file "${rel_path}"
done

require_executable "scripts/build-release-bundle.sh"
require_executable "scripts/verify-release-readiness.sh"

print_info "Checking committed-source reproducibility gate"
for rel_path in \
  README.md \
  install.sh \
  requirements.txt \
  ecosystem.config.js \
  amazon_scraper.py \
  browser_agent.py \
  eb_contracts.py \
  electronics_buyer.py \
  electronics_buyer_llm.py \
  main.py \
  manual_login.py \
  models.py \
  runtime_checks.py \
  stealth_utils.py \
  utils.py \
  .env.example; do
  require_committed_path "${rel_path}"
  RELEASE_TRACKED_FILES+=("${rel_path}")
done

for rel_path in docs scripts n8n-workflows; do
  collect_committed_dir_files "${rel_path}"
done

report_release_input_drift

print_info "Checking README release flow"
assert_contains "README.md" "## Supported Platform and Prerequisites"
assert_contains "README.md" "## Included in the Download"
assert_contains "README.md" "## You Must Provide Locally"
assert_contains "README.md" "## First-Run Sequence"
assert_contains "README.md" "bash install.sh"
assert_contains "README.md" "bash scripts/validate-env.sh"
assert_contains "README.md" "bash scripts/services-up.sh"
assert_contains "README.md" "bash scripts/services-status.sh"
assert_contains "README.md" "bash scripts/verify-runtime-operations.sh"
assert_contains "README.md" "bash scripts/verify-n8n-workflow-contract.sh"
assert_contains "README.md" "SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh"
assert_contains "README.md" "bash scripts/collect-diagnostics.sh"
assert_contains "README.md" "Env Validation PASS"
assert_contains "README.md" "Env Validation PENDING"
assert_before "README.md" "bash install.sh" "bash scripts/validate-env.sh"
assert_before "README.md" "bash scripts/validate-env.sh" "bash scripts/services-up.sh"

print_info "Checking install/env sequencing docs"
assert_contains "docs/INSTALL.md" "Env Validation PASS"
assert_contains "docs/INSTALL.md" "Env Validation PENDING"
assert_contains "docs/INSTALL.md" "bash scripts/validate-env.sh"
assert_contains "docs/INSTALL.md" "bash scripts/services-up.sh"
assert_before "docs/INSTALL.md" "bash install.sh" "bash scripts/validate-env.sh"
assert_before "docs/INSTALL.md" "bash scripts/validate-env.sh" "bash scripts/services-up.sh"
assert_contains "docs/ENVIRONMENT.md" "Env Validation PENDING"
assert_contains "docs/ENVIRONMENT.md" "bash install.sh"
assert_contains "docs/ENVIRONMENT.md" "bash scripts/validate-env.sh"
assert_contains "docs/ENVIRONMENT.md" "bash scripts/services-up.sh"
assert_before "docs/ENVIRONMENT.md" "bash install.sh" "bash scripts/validate-env.sh"
assert_before "docs/ENVIRONMENT.md" "bash scripts/validate-env.sh" "bash scripts/services-up.sh"

print_info "Checking release maintainer docs"
assert_contains "docs/RELEASE.md" "macOS on Apple Silicon"
assert_contains "docs/RELEASE.md" "bash scripts/build-release-bundle.sh --version v1.0.0"
assert_contains "docs/RELEASE.md" "shared cloud folder"
assert_contains "docs/RELEASE.md" ".env.example"
assert_contains "docs/RELEASE.md" ".env"
assert_contains "docs/RELEASE.md" "committed at `HEAD`"
assert_contains "docs/RELEASE.md" "fail if any required release input is untracked"
assert_contains "docs/RELEASE.md" "ignore dirty local-only changes"

print_info "Checking release checklist gate"
assert_contains "docs/RELEASE_CHECKLIST.md" "**Release version:**"
assert_contains "docs/RELEASE_CHECKLIST.md" "**Checklist run date:**"
assert_contains "docs/RELEASE_CHECKLIST.md" "NO SHIP"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash scripts/audit-bundle.sh --archive"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash install.sh"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash scripts/services-up.sh"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash scripts/services-status.sh"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash scripts/verify-runtime-operations.sh"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash scripts/verify-n8n-workflow-contract.sh"
assert_contains "docs/RELEASE_CHECKLIST.md" "SMOKE_ORDER_NUMBER=111-2222222-3333333 bash scripts/verify-smoke-readiness.sh"
assert_contains "docs/RELEASE_CHECKLIST.md" "bash scripts/collect-diagnostics.sh"

if [[ -n "${archive_path}" ]]; then
  print_info "Auditing archive ${archive_path}"
  if ! bash "${SCRIPT_DIR}/audit-bundle.sh" --archive "${archive_path}"; then
    failures=1
  fi
fi

if [[ "${failures}" -ne 0 ]]; then
  print_fail "Release readiness verification failed."
  print_remediation "Fix the missing docs/scripts or command references, then rerun bash scripts/verify-release-readiness.sh."
  exit 1
fi

print_pass "Release readiness verification passed."
print_info "Next: Complete docs/RELEASE_CHECKLIST.md for the version you plan to ship."
