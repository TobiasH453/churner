#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="${1:-venv39}"

cd "$ROOT_DIR"

echo "Using Python: $(/usr/bin/python3 --version)"
echo "Creating virtualenv at: $ROOT_DIR/$ENV_DIR"
/usr/bin/python3 -m venv "$ENV_DIR"

"$ENV_DIR/bin/python3" -m pip install --upgrade pip
"$ENV_DIR/bin/pip" install -r requirements.txt

echo
echo "Environment ready."
echo "Activate with:"
echo "  source $ENV_DIR/bin/activate"
echo "Verify with:"
echo "  python --version"
