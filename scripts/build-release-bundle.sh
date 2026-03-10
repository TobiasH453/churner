#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/build-release-bundle.sh --version v1.0.0 [--output-dir dist]

Options:
  --version, -v    Release version in vX.Y.Z format
  --output-dir     Directory for staged release folder and zip archive (default: dist)
  --help, -h       Show this help text

Environment:
  RELEASE_VERSION  Alternative to --version
USAGE
}

require_file() {
  local path="$1"
  if [[ ! -e "${REPO_ROOT}/${path}" ]]; then
    print_fail "Missing required release input: ${path}"
    print_remediation "Restore ${path} and rerun the release build."
    exit 1
  fi
}

require_committed_path() {
  local path="$1"
  if ! git -C "${REPO_ROOT}" cat-file -e "HEAD:${path}" 2>/dev/null; then
    print_fail "Required release input is not committed at HEAD: ${path}"
    print_remediation "Commit ${path}, then rerun the release build."
    exit 1
  fi
}

collect_committed_dir_files() {
  local dir_path="$1"
  local tracked_files=()
  local tracked_file

  require_file "${dir_path}"
  require_committed_path "${dir_path}"
  while IFS= read -r tracked_file; do
    tracked_files+=("${tracked_file}")
  done < <(git -C "${REPO_ROOT}" ls-tree -r --name-only HEAD -- "${dir_path}")

  if (( ${#tracked_files[@]} == 0 )); then
    print_fail "Required release directory has no committed contents at HEAD: ${dir_path}"
    print_remediation "Commit the required files under ${dir_path}, then rerun the release build."
    exit 1
  fi

  RELEASE_TRACKED_FILES+=("${tracked_files[@]}")
}
write_release_manifest() {
  cat >"${STAGE_ROOT}/RELEASE_MANIFEST.txt" <<EOF
release_version=${RELEASE_VERSION}
platform=macos-apple-silicon
archive_name=${ARCHIVE_NAME}
build_created_at=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
canonical_readme=README.md
included_roots=README.md install.sh requirements.txt ecosystem.config.js .env .env.example docs/ scripts/ n8n-workflows/
excluded_local_state=.n8n/ .pm2/ logs/ diagnostics/ data/browser-profile*/
EOF
}

RELEASE_VERSION="${RELEASE_VERSION:-}"
OUTPUT_DIR="${REPO_ROOT}/dist"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --version|-v)
      RELEASE_VERSION="${2:-}"
      shift 2
      ;;
    --output-dir)
      OUTPUT_DIR="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      print_fail "Unknown argument: $1"
      print_remediation "Run bash scripts/build-release-bundle.sh --help"
      exit 1
      ;;
  esac
done

if [[ -z "${RELEASE_VERSION}" ]]; then
  print_fail "Release version is required."
  print_remediation "Run bash scripts/build-release-bundle.sh --version v1.0.0"
  exit 1
fi

if [[ ! "${RELEASE_VERSION}" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
  print_fail "Invalid release version: ${RELEASE_VERSION}"
  print_remediation "Use semantic version format like v1.0.0."
  exit 1
fi

if [[ "${OUTPUT_DIR}" != /* ]]; then
  OUTPUT_DIR="${REPO_ROOT}/${OUTPUT_DIR}"
fi

require_command "zip" "Install zip and rerun the release build."
require_command "unzip" "Install unzip and rerun the release build."

RELEASE_SLUG="1step-cashouts-${RELEASE_VERSION}-macos-apple-silicon"
STAGE_ROOT="${OUTPUT_DIR}/${RELEASE_SLUG}"
ARCHIVE_NAME="${RELEASE_SLUG}.zip"
ARCHIVE_PATH="${OUTPUT_DIR}/${ARCHIVE_NAME}"

if [[ -e "${STAGE_ROOT}" || -e "${ARCHIVE_PATH}" ]]; then
  print_fail "Release output already exists for ${RELEASE_VERSION}."
  print_remediation "Remove ${STAGE_ROOT} and ${ARCHIVE_PATH}, or choose a different --output-dir/version."
  exit 1
fi

REQUIRED_ROOT_FILES=(
  README.md
  install.sh
  requirements.txt
  ecosystem.config.js
  amazon_scraper.py
  browser_agent.py
  eb_contracts.py
  electronics_buyer.py
  electronics_buyer_llm.py
  main.py
  manual_login.py
  models.py
  runtime_checks.py
  stealth_utils.py
  utils.py
  .env.example
)

REQUIRED_ROOT_DIRS=(
  docs
  scripts
  n8n-workflows
)
RELEASE_TRACKED_FILES=()

print_info "Preparing release bundle for ${RELEASE_VERSION}"
mkdir -p "${OUTPUT_DIR}"

for rel_path in "${REQUIRED_ROOT_FILES[@]}"; do
  require_file "${rel_path}"
  require_committed_path "${rel_path}"
  RELEASE_TRACKED_FILES+=("${rel_path}")
done

for rel_path in "${REQUIRED_ROOT_DIRS[@]}"; do
  collect_committed_dir_files "${rel_path}"
done

print_info "Staging release files at ${STAGE_ROOT}"
mkdir -p "${STAGE_ROOT}"

git -C "${REPO_ROOT}" archive --format=tar HEAD "${RELEASE_TRACKED_FILES[@]}" | tar -xf - -C "${STAGE_ROOT}"

cp "${REPO_ROOT}/.env.example" "${STAGE_ROOT}/.env"
write_release_manifest

print_info "Creating zip archive ${ARCHIVE_PATH}"
(
  cd "${OUTPUT_DIR}"
  zip -qr "${ARCHIVE_NAME}" "${RELEASE_SLUG}"
)

print_info "Auditing generated archive"
bash "${SCRIPT_DIR}/audit-bundle.sh" --archive "${ARCHIVE_PATH}"

print_pass "Release bundle created: ${ARCHIVE_PATH}"
print_info "Staged directory: ${STAGE_ROOT}"
print_info "Next: Upload ${ARCHIVE_NAME} to the shared cloud release folder after checklist verification."
