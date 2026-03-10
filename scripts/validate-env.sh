#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${REPO_ROOT}/.env"
ALLOW_TEMPLATE_PLACEHOLDERS=0
TEMPLATE_PENDING_EXIT=20

errors=()
placeholder_keys=()

usage() {
  cat <<'USAGE'
Usage:
  bash scripts/validate-env.sh [--allow-template-placeholders] [path/to/.env]

Options:
  --allow-template-placeholders  Treat shipped placeholder values as "pending" instead of a hard failure.
  --help, -h                     Show this help text.
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --allow-template-placeholders)
      ALLOW_TEMPLATE_PLACEHOLDERS=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      ENV_FILE="$1"
      shift
      ;;
  esac
done

append_error() {
  errors+=("$1")
}

append_placeholder_key() {
  local key="$1"
  local existing
  if (( ${#placeholder_keys[@]} > 0 )); then
    for existing in "${placeholder_keys[@]}"; do
      if [[ "${existing}" == "${key}" ]]; then
        return 0
      fi
    done
  fi
  placeholder_keys+=("${key}")
}

trim_value() {
  local raw="$1"
  # shellcheck disable=SC2001
  raw="$(echo "${raw}" | sed -E 's/^[[:space:]]+//; s/[[:space:]]+$//')"
  if [[ ${#raw} -ge 2 ]]; then
    if [[ "${raw:0:1}" == '"' && "${raw: -1}" == '"' ]]; then
      raw="${raw:1:${#raw}-2}"
    elif [[ "${raw:0:1}" == "'" && "${raw: -1}" == "'" ]]; then
      raw="${raw:1:${#raw}-2}"
    fi
  fi
  echo "${raw}"
}

is_placeholder_value() {
  local value="$1"
  [[ "${value}" == replace-with-* ]]
}

get_env_key_value() {
  local key="$1"
  local line
  line="$(grep -E "^${key}=" "${ENV_FILE}" | tail -n 1 || true)"
  if [[ -z "${line}" ]]; then
    echo ""
    return 0
  fi
  trim_value "${line#*=}"
}

require_key() {
  local key="$1"
  local value
  value="$(get_env_key_value "${key}")"
  if [[ -z "${value}" ]]; then
    append_error "Missing required key: ${key}. Add it to .env and rerun validation."
  fi
}

validate_email_key() {
  local key="$1"
  local value
  value="$(get_env_key_value "${key}")"
  if is_placeholder_value "${value}"; then
    append_placeholder_key "${key}"
    return 0
  fi
  if [[ -n "${value}" && ! "${value}" =~ ^[^[:space:]@]+@[^[:space:]@]+\.[^[:space:]@]+$ ]]; then
    append_error "Invalid format for ${key}. Expected an email-style value."
  fi
}

validate_port_key() {
  local key="$1"
  local value
  value="$(get_env_key_value "${key}")"
  if [[ -z "${value}" ]]; then
    return 0
  fi
  if [[ ! "${value}" =~ ^[0-9]+$ ]]; then
    append_error "Invalid ${key}. Expected numeric port."
    return 0
  fi
  if (( value < 1 || value > 65535 )); then
    append_error "Invalid ${key}. Expected port in range 1-65535."
  fi
}

validate_boolean_key() {
  local key="$1"
  local value
  value="$(get_env_key_value "${key}")"
  if [[ -z "${value}" ]]; then
    return 0
  fi
  case "${value}" in
    true|false|TRUE|FALSE|1|0|yes|no|YES|NO)
      ;;
    *)
      append_error "Invalid ${key}. Use true/false style value."
      ;;
  esac
}

validate_account_type_optional() {
  local key="DEFAULT_ACCOUNT_TYPE"
  local value
  value="$(get_env_key_value "${key}")"
  if [[ -z "${value}" ]]; then
    return 0
  fi
  case "${value}" in
    amz_personal|amz_business)
      ;;
    *)
      append_error "Invalid ${key}. Allowed values: amz_personal, amz_business."
      ;;
  esac
}

validate_anthropic_key() {
  local value
  value="$(get_env_key_value "ANTHROPIC_API_KEY")"
  if [[ -z "${value}" ]]; then
    return 0
  fi
  if is_placeholder_value "${value}"; then
    append_placeholder_key "ANTHROPIC_API_KEY"
    return 0
  fi
  if [[ ! "${value}" =~ ^sk-ant- ]]; then
    append_error "ANTHROPIC_API_KEY appears malformed. Expected prefix sk-ant-."
  fi
  if (( ${#value} < 40 )); then
    append_error "ANTHROPIC_API_KEY appears too short. Use a full Anthropic key."
  fi
}

collect_placeholder_required_keys() {
  local key
  local value
  for key in "${required_keys[@]}"; do
    value="$(get_env_key_value "${key}")"
    if is_placeholder_value "${value}"; then
      append_placeholder_key "${key}"
    fi
  done
}

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "[FAIL] Missing .env file."
  echo "Create it with: cp .env.example .env"
  echo "Then edit .env locally and rerun: bash scripts/validate-env.sh"
  exit 1
fi

required_keys=(
  "ANTHROPIC_API_KEY"
  "AMAZON_EMAIL"
  "AMAZON_PASSWORD"
  "AMAZON_BUSINESS_EMAIL"
  "AMAZON_BUSINESS_PASSWORD"
  "EB_LOGIN_EMAIL"
  "SERVER_PORT"
  "N8N_PORT"
)

for key in "${required_keys[@]}"; do
  require_key "${key}"
done

validate_anthropic_key
validate_email_key "AMAZON_EMAIL"
validate_email_key "AMAZON_BUSINESS_EMAIL"
validate_email_key "EB_LOGIN_EMAIL"
validate_port_key "SERVER_PORT"
validate_port_key "N8N_PORT"
validate_boolean_key "BROWSER_HEADLESS"
validate_account_type_optional
collect_placeholder_required_keys

if (( ${#errors[@]} == 0 && ${#placeholder_keys[@]} > 0 )); then
  if [[ "${ALLOW_TEMPLATE_PLACEHOLDERS}" -eq 1 ]]; then
    echo "[WARN] Environment template still contains placeholder values for ${#placeholder_keys[@]} required key(s):"
    for key in "${placeholder_keys[@]}"; do
      echo "  - ${key}"
    done
    echo
    echo "Edit .env locally, then rerun:"
    echo "  bash scripts/validate-env.sh"
    exit "${TEMPLATE_PENDING_EXIT}"
  fi

  for key in "${placeholder_keys[@]}"; do
    append_error "Placeholder value still present for ${key}. Edit .env locally and rerun validation."
  done
fi

if (( ${#errors[@]} > 0 )); then
  echo "[FAIL] Environment validation failed with ${#errors[@]} issue(s):"
  for item in "${errors[@]}"; do
    echo "  - ${item}"
  done
  echo
  echo "Fix the listed key names in .env, then rerun:"
  echo "  bash scripts/validate-env.sh"
  exit 1
fi

echo "[PASS] Environment validation succeeded. Required keys are present and format checks passed."
exit 0
