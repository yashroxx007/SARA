#!/usr/bin/env bash
# Launch SARA: ensure the local MLX model server is up, then start the assistant.
# Usage:  ./run.sh
#
# The MLX server runs in its own venv (~/mlx-server, Python 3.12) because MLX
# has no wheels for SARA's 3.14 venv. This script starts it detached if needed,
# waits until it answers, then launches SARA in the foreground.

set -euo pipefail

SERVER_VENV="$HOME/mlx-server"
SARA_DIR="$HOME/SARA"
PORT=8080
LOG="$HOME/mlx-server.log"
BASE="http://localhost:$PORT/v1/models"

if curl -s "$BASE" >/dev/null 2>&1; then
  echo "[run] MLX server already up on :$PORT"
else
  echo "[run] Starting MLX server (logs -> $LOG)..."
  ( source "$SERVER_VENV/bin/activate" && nohup mlx-omni-server --port "$PORT" --log-level warning > "$LOG" 2>&1 & )
  for _ in $(seq 1 30); do
    if curl -s "$BASE" >/dev/null 2>&1; then break; fi
    sleep 1
  done
  if curl -s "$BASE" >/dev/null 2>&1; then
    echo "[run] MLX server up."
  else
    echo "[run] MLX server didn't come up in 30s — check $LOG" >&2
    exit 1
  fi
fi

cd "$SARA_DIR"
source .venv-1/bin/activate
exec python main.py
