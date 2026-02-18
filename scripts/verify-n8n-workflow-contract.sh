#!/usr/bin/env bash

set -euo pipefail

SCRIPT_PATH="${BASH_SOURCE[0]}"
SCRIPT_DIR="${SCRIPT_PATH%/*}"
if [ "$SCRIPT_DIR" = "$SCRIPT_PATH" ]; then
  SCRIPT_DIR="."
fi
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
WORKFLOW_JSON="$ROOT_DIR/n8n-workflows/03-process-order-v1.0.0.json"
TEST_SCRIPT="$ROOT_DIR/test_n8n_process_order_contract.py"

info() {
  echo "[INFO] $1"
}

pass() {
  echo "[PASS] $1"
}

fail() {
  echo "[FAIL] $1"
}

next_step() {
  echo "Next: $1"
}

if ! command -v python3 >/dev/null 2>&1; then
  fail "Missing dependency: python3"
  next_step "Install Python 3 and rerun: bash scripts/verify-n8n-workflow-contract.sh"
  exit 1
fi

if [ ! -f "$WORKFLOW_JSON" ]; then
  fail "Missing workflow artifact: n8n-workflows/03-process-order-v1.0.0.json"
  next_step "Generate or restore the canonical workflow artifact, then rerun this command"
  exit 1
fi

if [ ! -f "$TEST_SCRIPT" ]; then
  fail "Missing contract test: test_n8n_process_order_contract.py"
  next_step "Restore the test file and rerun this command"
  exit 1
fi

info "Validating workflow JSON syntax..."
if ! python3 -m json.tool "$WORKFLOW_JSON" >/dev/null 2>&1; then
  fail "Workflow JSON is invalid."
  next_step "Fix JSON syntax in n8n-workflows/03-process-order-v1.0.0.json"
  exit 1
fi
pass "Workflow JSON syntax check passed."

info "Running static workflow contract checks..."
if ! (cd "$ROOT_DIR" && python3 test_n8n_process_order_contract.py); then
  fail "Workflow contract checks failed."
  next_step "Review test output, align workflow mapping/defaults, then rerun this command"
  exit 1
fi
pass "Workflow contract checks passed."

pass "n8n workflow contract verification passed."
exit 0
