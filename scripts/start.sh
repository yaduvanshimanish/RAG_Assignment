#!/bin/bash
set -e

echo "[start.sh] Ensuring /app/data directories exist and are writable..."
mkdir -p /app/data/uploads /app/data/faiss_index

# If running as root (Railway default), fix ownership and drop to appuser.
# If already running as appuser (local Docker), just start directly.
if [ "$(id -u)" = "0" ]; then
    echo "[start.sh] Running as root. Fixing ownership for appuser (uid=1000)..."
    chown -R 1000:1000 /app/data
    echo "[start.sh] Starting uvicorn as appuser..."
    exec gosu 1000 uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
else
    echo "[start.sh] Running as non-root user (uid=$(id -u)). Starting uvicorn..."
    exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 1
fi
