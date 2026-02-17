#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${1:-${REPO_ROOT}/.env}"

errors=()

append_error() {
  errors+=("$1")
}

trim_value() {
  local raw="$1"
  # shellcheck disable=SC2001
  raw="$(echo "${raw}" | sed -E 's/^\s+//; s/\s+$//')"
  if [[ ${#raw} -ge 2 ]]; then
    if [[ "${raw:0:1}" == '"' && "${raw: -1}" == '"' ]]; then
      raw="${raw:1:${#raw}-2}"
    elif [[ "${raw:0:1}" == "'" && "${raw: -1}" == "'" ]]; then
      raw="${raw:1:${#raw}-2}"
    fi
  fi
  echo "${raw}"
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
  if [[ ! "${value}" =~ ^sk-ant- ]]; then
    append_error "ANTHROPIC_API_KEY appears malformed. Expected prefix sk-ant-."
  fi
  if (( ${#value} < 40 )); then
    append_error "ANTHROPIC_API_KEY appears too short. Use a full Anthropic key."
  fi
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
