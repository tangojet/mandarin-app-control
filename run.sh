#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <agent-dir>" >&2
  exit 1
fi

AGENT_DIR="$(cd "$(dirname "$0")/$1" && pwd)"

# Load .env if present
if [[ -f "$AGENT_DIR/.env" ]]; then
  set -a; source "$AGENT_DIR/.env"; set +a
fi

export PYTHONPATH="$(dirname "$0"):${PYTHONPATH:-}"

# Pick a Python interpreter: $PYTHON override, else python3, else python.
PYTHON_BIN="${PYTHON:-}"
if [[ -z "$PYTHON_BIN" ]]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN=python3
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN=python
  else
    echo "No python interpreter found (set \$PYTHON)" >&2
    exit 1
  fi
fi

exec "$PYTHON_BIN" "$AGENT_DIR/main.py"
