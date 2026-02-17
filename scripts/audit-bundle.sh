#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
BUNDLEIGNORE_FILE="${REPO_ROOT}/.bundleignore"

usage() {
  cat <<USAGE
Usage:
  bash scripts/audit-bundle.sh
  bash scripts/audit-bundle.sh --file-list /path/to/files.txt
  bash scripts/audit-bundle.sh --archive /path/to/archive.tar.gz

Modes:
  default      audits git-tracked files in the current repository
  --file-list  audits newline-delimited file paths
  --archive    audits archive entries (.tar/.tar.gz/.tgz/.zip)
USAGE
}

normalize_path() {
  local path="$1"
  path="${path#./}"
  path="${path#${REPO_ROOT}/}"
  printf '%s\n' "${path}"
}

collect_default_paths() {
  (cd "${REPO_ROOT}" && git ls-files)
}

collect_file_list_paths() {
  local file_list="$1"
  if [[ ! -f "${file_list}" ]]; then
    echo "ERROR: file list not found: ${file_list}" >&2
    exit 1
  fi
  cat "${file_list}"
}

collect_archive_paths() {
  local archive_path="$1"
  if [[ ! -f "${archive_path}" ]]; then
    echo "ERROR: archive not found: ${archive_path}" >&2
    exit 1
  fi

  case "${archive_path}" in
    *.zip)
      unzip -Z1 "${archive_path}"
      ;;
    *.tar|*.tar.gz|*.tgz|*.tar.bz2|*.tbz2|*.tar.xz|*.txz)
      tar -tf "${archive_path}"
      ;;
    *)
      echo "ERROR: unsupported archive format: ${archive_path}" >&2
      exit 1
      ;;
  esac
}

SOURCE_MODE="default"
SOURCE_VALUE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --file-list)
      SOURCE_MODE="file_list"
      SOURCE_VALUE="${2:-}"
      shift 2
      ;;
    --archive)
      SOURCE_MODE="archive"
      SOURCE_VALUE="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      echo "ERROR: unknown argument: $1" >&2
      usage
      exit 1
      ;;
  esac
done

if [[ ! -f "${BUNDLEIGNORE_FILE}" ]]; then
  echo "ERROR: missing .bundleignore at ${BUNDLEIGNORE_FILE}" >&2
  exit 1
fi

paths_tmp="$(mktemp -t audit-bundle-paths.XXXXXX)"
trap 'rm -f "$paths_tmp"' EXIT

case "${SOURCE_MODE}" in
  default)
    collect_default_paths >"${paths_tmp}"
    ;;
  file_list)
    collect_file_list_paths "${SOURCE_VALUE}" >"${paths_tmp}"
    ;;
  archive)
    collect_archive_paths "${SOURCE_VALUE}" >"${paths_tmp}"
    ;;
esac

normalized_tmp="$(mktemp -t audit-bundle-normalized.XXXXXX)"
trap 'rm -f "$paths_tmp" "$normalized_tmp"' EXIT

while IFS= read -r path; do
  [[ -z "${path}" ]] && continue
  normalize_path "${path}" >>"${normalized_tmp}"
done <"${paths_tmp}"

patterns_tmp="$(mktemp -t audit-bundle-patterns.XXXXXX)"
trap 'rm -f "$paths_tmp" "$normalized_tmp" "$patterns_tmp"' EXIT

grep -Ev '^\s*($|#)' "${BUNDLEIGNORE_FILE}" >"${patterns_tmp}"

matches_pattern() {
  local path="$1"
  local pattern="$2"

  if [[ "${pattern}" == */ ]]; then
    local prefix="${pattern%/}"
    [[ "${path}" == "${prefix}" || "${path}" == "${prefix}/"* ]]
    return
  fi

  case "${path}" in
    ${pattern})
      return 0
      ;;
    *)
      return 1
      ;;
  esac
}

blocked_paths=""
while IFS= read -r path; do
  [[ -z "${path}" ]] && continue
  while IFS= read -r pattern; do
    [[ -z "${pattern}" ]] && continue
    if matches_pattern "${path}" "${pattern}"; then
      blocked_paths+="${path}"$'\n'
      break
    fi
  done <"${patterns_tmp}"
done <"${normalized_tmp}"

if [[ -n "${blocked_paths}" ]]; then
  echo "[FAIL] Bundle audit failed. Forbidden paths detected:"
  printf '%s' "${blocked_paths}" | sed '/^$/d; s/^/  - /'
  echo
  echo "Update the candidate bundle and rerun:"
  echo "  bash scripts/audit-bundle.sh"
  exit 1
fi

echo "[PASS] Bundle audit passed. No forbidden paths matched .bundleignore."
exit 0
