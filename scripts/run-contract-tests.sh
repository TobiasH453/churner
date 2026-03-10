#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

resolve_python_bin() {
  local candidate
  local candidates=(
    "${ROOT_DIR}/venv/bin/python"
    "${ROOT_DIR}/venv314/bin/python"
    "${ROOT_DIR}/venv313/bin/python"
    "${ROOT_DIR}/venv312/bin/python"
    "python3"
  )

  for candidate in "${candidates[@]}"; do
    if [[ "${candidate}" == */* ]]; then
      [[ -x "${candidate}" ]] && { echo "${candidate}"; return 0; }
    elif command -v "${candidate}" >/dev/null 2>&1; then
      command -v "${candidate}"
      return 0
    fi
  done

  return 1
}

if PYTHON_BIN="${PYTHON_BIN:-$(resolve_python_bin 2>/dev/null || true)}" && [[ -n "${PYTHON_BIN}" ]]; then
  :
else
  echo "[FAIL] Missing dependency: python3" >&2
  echo "       Next: Create a local virtualenv or install Python 3, then rerun bash scripts/run-contract-tests.sh" >&2
  exit 1
fi

TESTS=(
  test_amazon_account_routing_contract.py
  test_amazon_item_scope_contract.py
  test_amazon_shipping_date_normalization.py
  test_amazon_tracking_number_extraction.py
  test_eb_deal_contract.py
  test_eb_deals_readiness.py
  test_eb_tracking_contract.py
  test_n8n_process_order_contract.py
)

for test_file in "${TESTS[@]}"; do
  if [[ ! -f "$test_file" ]]; then
    echo "[WARN] Skipping missing contract test: $test_file"
    continue
  fi

  echo "[INFO] Running $test_file"
  PYTHONPYCACHEPREFIX="${PYTHONPYCACHEPREFIX:-/tmp/pyc}" "$PYTHON_BIN" "$test_file"
done

echo "[PASS] Contract test suite completed."
