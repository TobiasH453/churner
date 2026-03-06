#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
source "${SCRIPT_DIR}/service-env.sh"

LINES_DEFAULT=120
ARCHIVE_ENABLED=1
OUTPUT_BASE="${REPO_ROOT}/diagnostics"
CAPTURE_TIMEOUT=12
FORBIDDEN_PATH_PATTERNS=".env|browser-profile|\\.n8n|\\.pm2"

usage() {
  cat <<'USAGE'
Usage: bash scripts/collect-diagnostics.sh [--output-dir DIR] [--lines N] [--timeout SEC] [--no-archive]

Collects a deterministic diagnostics snapshot for support triage.

Options:
  --output-dir DIR   Base directory for diagnostics output (default: ./diagnostics)
  --lines N          Max lines per log snapshot (default: 120)
  --timeout SEC      Per-command capture timeout seconds (default: 12)
  --no-archive       Keep directory only (skip .tar.gz archive)
  -h, --help         Show this help
USAGE
}

redact_stream() {
  sed -E \
    -e 's/(Authorization:[[:space:]]*Bearer[[:space:]]+)[^[:space:]]+/\1[REDACTED]/Ig' \
    -e 's/(set-cookie:[[:space:]]*)[^;]+/\1[REDACTED]/Ig' \
    -e 's/((^|[[:space:]])(API_KEY|SECRET|TOKEN|PASSWORD|PASS|COOKIE|SESSION)[^=:{ ]*[=:][[:space:]]*)[^[:space:]]+/\1[REDACTED]/Ig'
}

run_with_timeout() {
  local timeout_sec="$1"
  local outfile="$2"
  shift 2

  set +e
  "$@" >"${outfile}" 2>&1 &
  local cmd_pid=$!
  local elapsed=0

  while kill -0 "${cmd_pid}" 2>/dev/null; do
    if [[ "${elapsed}" -ge "${timeout_sec}" ]]; then
      kill "${cmd_pid}" >/dev/null 2>&1 || true
      wait "${cmd_pid}" >/dev/null 2>&1 || true
      printf '[WARN] command timed out after %ss\n' "${timeout_sec}" >>"${outfile}"
      return 124
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done

  wait "${cmd_pid}"
  local cmd_exit=$?
  return "${cmd_exit}"
}

capture_command() {
  local outfile="$1"
  local timeout_sec="$2"
  shift 2

  local raw_out
  raw_out="$(mktemp)"
  set +e
  run_with_timeout "${timeout_sec}" "${raw_out}" "$@"
  local cmd_exit=$?
  set -e

  {
    echo "command: $*"
    echo "exit_code: ${cmd_exit}"
    echo "captured_at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
    echo ""
    cat "${raw_out}" | redact_stream
  } >"${outfile}.tmp"
  mv "${outfile}.tmp" "${outfile}"
  rm -f "${raw_out}"
}

write_redaction_probe() {
  {
    echo "sample_input:"
    echo "API_KEY=example-123"
    echo "Authorization: Bearer token-xyz"
    echo "set-cookie: sessionid=abcd; path=/"
    echo ""
    echo "sample_output:"
    printf 'API_KEY=example-123\nAuthorization: Bearer token-xyz\nset-cookie: sessionid=abcd; path=/\n' | redact_stream
  } > "$1"
}

write_exclusion_audit() {
  local outfile="$1"
  {
    echo "forbidden_path_patterns=${FORBIDDEN_PATH_PATTERNS}"
    if find "${OUT_DIR}" -type f | rg -q "${FORBIDDEN_PATH_PATTERNS}"; then
      echo "status=fail"
      echo "details=forbidden file pattern found in diagnostics output"
    else
      echo "status=pass"
      echo "details=no forbidden file patterns found in diagnostics output"
    fi
  } > "${outfile}"
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

while [[ $# -gt 0 ]]; do
  case "$1" in
    --output-dir)
      OUTPUT_BASE="$2"
      shift 2
      ;;
    --lines)
      if [[ -z "${2:-}" ]]; then
        print_fail "Missing value for --lines"
        usage
        exit 1
      fi
      LINES_DEFAULT="$2"
      shift 2
      ;;
    --timeout)
      if [[ -z "${2:-}" ]]; then
        print_fail "Missing value for --timeout"
        usage
        exit 1
      fi
      CAPTURE_TIMEOUT="$2"
      shift 2
      ;;
    --no-archive)
      ARCHIVE_ENABLED=0
      shift
      ;;
    *)
      print_fail "Unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if ! is_positive_integer "${LINES_DEFAULT}"; then
  print_fail "Line count must be a positive integer. Received: ${LINES_DEFAULT}"
  print_remediation "Run: bash scripts/collect-diagnostics.sh --lines 120"
  exit 1
fi

if ! is_positive_integer "${CAPTURE_TIMEOUT}"; then
  print_fail "Timeout must be a positive integer. Received: ${CAPTURE_TIMEOUT}"
  print_remediation "Run: bash scripts/collect-diagnostics.sh --timeout 12"
  exit 1
fi

TS="$(date +%Y%m%d-%H%M%S)"
OUT_DIR="${OUTPUT_BASE}/diag-${TS}"
CMD_DIR="${OUT_DIR}/commands"
LOG_DIR="${OUT_DIR}/logs"
SYS_DIR="${OUT_DIR}/system"

mkdir -p "${CMD_DIR}" "${LOG_DIR}" "${SYS_DIR}"

print_info "Collecting diagnostics in ${OUT_DIR}"

capture_command "${CMD_DIR}/git-status.txt" "${CAPTURE_TIMEOUT}" git status --short
capture_command "${CMD_DIR}/services-status.txt" "${CAPTURE_TIMEOUT}" bash "${SCRIPT_DIR}/services-status.sh"
capture_command "${CMD_DIR}/verify-runtime-operations-help.txt" "${CAPTURE_TIMEOUT}" bash "${SCRIPT_DIR}/verify-runtime-operations.sh" --help
capture_command "${CMD_DIR}/verify-smoke-readiness-help.txt" "${CAPTURE_TIMEOUT}" bash "${SCRIPT_DIR}/verify-smoke-readiness.sh" --help
capture_command "${CMD_DIR}/verify-n8n-workflow-contract.txt" "${CAPTURE_TIMEOUT}" bash "${SCRIPT_DIR}/verify-n8n-workflow-contract.sh"

capture_command "${LOG_DIR}/amazon-agent.log" "${CAPTURE_TIMEOUT}" pm2 logs "${AMAZON_AGENT_PM2_NAME}" --lines "${LINES_DEFAULT}" --nostream
capture_command "${LOG_DIR}/n8n-server.log" "${CAPTURE_TIMEOUT}" pm2 logs "${N8N_PM2_NAME}" --lines "${LINES_DEFAULT}" --nostream

capture_command "${SYS_DIR}/versions.txt" "${CAPTURE_TIMEOUT}" bash -lc 'bash --version | head -1; python3 --version; node --version; pm2 --version'
write_redaction_probe "${SYS_DIR}/redaction-probe.txt"
write_exclusion_audit "${SYS_DIR}/exclusion-audit.txt"

{
  echo "captured_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo_root=${REPO_ROOT}"
  echo "server_port=${SERVER_PORT}"
  echo "n8n_port=${N8N_PORT}"
  echo "pm2_home=${PM2_HOME}"
  echo "n8n_user_folder=${N8N_USER_FOLDER}"
  echo "logs_line_cap=${LINES_DEFAULT}"
  echo "capture_timeout_sec=${CAPTURE_TIMEOUT}"
  echo "archive_enabled=${ARCHIVE_ENABLED}"
} > "${SYS_DIR}/environment-safe.txt"

{
  echo "diagnostics_bundle=${OUT_DIR}"
  echo "generated_at_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "excluded_paths=.env,data/browser-profile*,data/browser-profile-business*,.n8n,.pm2"
  echo "forbidden_path_patterns=${FORBIDDEN_PATH_PATTERNS}"
  echo "redaction=enabled(secret-like values replaced with [REDACTED])"
  echo "contents:"
  find "${OUT_DIR}" -type f | sed "s#${OUT_DIR}/#- #"
} > "${OUT_DIR}/manifest.txt"

if [[ "${ARCHIVE_ENABLED}" -eq 1 ]]; then
  ARCHIVE_PATH="${OUT_DIR}.tar.gz"
  tar -czf "${ARCHIVE_PATH}" -C "$(dirname "${OUT_DIR}")" "$(basename "${OUT_DIR}")"
  print_pass "Diagnostics archive created: ${ARCHIVE_PATH}"
fi

print_pass "Diagnostics collected: ${OUT_DIR}"
print_info "Share this directory (or archive) for support review."
