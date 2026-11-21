#!/usr/bin/env bash
# Unit tests + static checks of the generated backend.
#   run_unittests_python.sh <build folder>
# Exit 0: tests and checks pass. Exit 80: tests pass, only ruff/mypy fail. Other: tests fail.
set -uo pipefail
BUILD="$(cd "${1:?usage: run_unittests_python.sh <build>}" && pwd)"
cd "$BUILD" || exit 1
command -v uv >/dev/null || { echo "uv: command not found"; exit 127; }


uv sync --all-groups --quiet || { echo "uv sync failed"; exit 1; }

APP_KEEP_DB=1 uv run pytest -q -p no:cacheprovider
status=$?
[ "$status" -eq 5 ] && { echo "no unit tests were collected"; exit 1; }
[ "$status" -ne 0 ] && exit "$status"

checks=0
uv run ruff format --check . || checks=1
uv run ruff check . || checks=1
uv run mypy || checks=1
[ "$checks" -ne 0 ] && { echo "unit tests pass; static checks fail"; exit 80; }
exit 0
