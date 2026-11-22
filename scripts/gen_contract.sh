#!/usr/bin/env bash
# Re-export the OpenAPI contract and regenerate the TypeScript types.
# With --check: fail if either file would change (contract drift).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
uv run --project backend_turri python scripts/export_openapi.py
# openapi-typescript needs TypeScript 5 (the app uses 7), so it runs outside the project.
(cd "${TMPDIR:-/tmp}" && npx -y -p typescript@5 -p openapi-typescript@7 openapi-typescript \
  "$ROOT/contracts/openapi.json" -o "$ROOT/frontend/src/client/schema.d.ts")
if [[ "${1:-}" == "--check" ]]; then
  git diff --exit-code -- contracts/openapi.json frontend/src/client/schema.d.ts \
    || { echo "Contract drift: commit the regenerated files." >&2; exit 1; }
fi
