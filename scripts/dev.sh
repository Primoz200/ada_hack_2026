#!/usr/bin/env bash
# Start backend (:8000) and frontend (https://<ip>:5173, proxies /api) for local development.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
trap 'kill 0' EXIT
(cd "$ROOT/backend" && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload) &
(cd "$ROOT/frontend" && npm run dev) &
wait
