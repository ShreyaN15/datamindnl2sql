#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

PORT="${PORT:-3001}"
PY="${PYTHON:-python3}"
VENV=".venv"

if [[ ! -d "$VENV" ]]; then
  "$PY" -m venv "$VENV"
fi
# shellcheck disable=SC1091
source "$VENV/bin/activate"
# Use the venv interpreter so pip and runtime match (avoids broken mixed 3.13/3.14 installs).
python3 -m pip install -q -r requirements.txt

exec uvicorn main:app --host 0.0.0.0 --port "$PORT"
