#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_DIR="${1:-venv}"

cd "$ROOT_DIR"

pick_python() {
  local candidates=(
    "python3.13"
    "python3.12"
    "python3.11"
    "python3.14"
    "/opt/homebrew/opt/python@3.13/bin/python3.13"
    "/opt/homebrew/opt/python@3.12/bin/python3.12"
    "/opt/homebrew/opt/python@3.11/bin/python3.11"
    "/opt/homebrew/opt/python@3.14/bin/python3.14"
  )
  local py

  for py in "${candidates[@]}"; do
    if command -v "$py" >/dev/null 2>&1; then
      local ver
      ver="$($py - <<'PY'
import sys
print(f"{sys.version_info.major}.{sys.version_info.minor}")
PY
)"
      case "$ver" in
        3.11|3.12|3.13|3.14)
          echo "$py"
          return 0
          ;;
      esac
    fi
  done

  return 1
}

PYTHON_BIN="$(pick_python || true)"

if [[ -z "$PYTHON_BIN" ]]; then
  echo "ERROR: Supported Python not found." >&2
  echo "Preferred version: Python 3.13." >&2
  echo "Fallback versions: 3.12 or 3.11." >&2
  echo >&2
  echo "Install Python 3.13 on macOS:" >&2
  echo "  brew install python@3.13" >&2
  echo >&2
  echo "Then rerun:" >&2
  echo "  ./scripts/rebuild_venv.sh $ENV_DIR" >&2
  exit 1
fi

echo "Using Python: $($PYTHON_BIN --version)"
echo "Creating virtualenv at: $ROOT_DIR/$ENV_DIR"
"$PYTHON_BIN" -m venv "$ENV_DIR"

"$ENV_DIR/bin/python3" -m pip install --upgrade pip
"$ENV_DIR/bin/pip" install -r requirements.txt

echo
echo "Environment ready."
echo "Activate with:"
echo "  source $ENV_DIR/bin/activate"
echo "Verify with:"
echo "  python --version"
