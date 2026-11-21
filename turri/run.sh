#!/usr/bin/env bash
# Load Bedrock credentials (kept outside the repo) and run turri in this folder.
#   ./run.sh doctor
#   ./run.sh regenerate backend.plain --build-dir ../backend_turri --report report.json
set -euo pipefail
ENV_FILE="${TURRI_ENV_FILE:-$HOME/.config/turri/bedrock.env}"
[ -f "$ENV_FILE" ] || { echo "missing $ENV_FILE (see turri/README.md)"; exit 2; }
set -a; . "$ENV_FILE"; set +a
cd "$(dirname "$0")"
export TURRI_COMMAND_TIMEOUT="${TURRI_COMMAND_TIMEOUT:-600}"
exec turri "$@"
