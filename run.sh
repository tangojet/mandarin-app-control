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

exec python "$AGENT_DIR/main.py"
