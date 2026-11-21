#!/usr/bin/env bash
# Black-box conformance tests of the generated backend.
#   run_conformance_tests_python.sh <build folder> <conformance tests folder>
# The tests start the service themselves from $BACKEND_BUILD_DIR (see ***test reqs***).
# Exit 0: tests and checks pass. Exit 80: tests pass, only ruff/mypy fail. Other: tests fail.
set -uo pipefail
BUILD="$(cd "${1:?usage: run_conformance_tests_python.sh <build> <tests>}" && pwd)"
TESTS="$(cd "${2:?usage: run_conformance_tests_python.sh <build> <tests>}" && pwd)"
command -v uv >/dev/null || { echo "uv: command not found"; exit 127; }


# the service under test
(cd "$BUILD" && uv sync --quiet) || { echo "uv sync of the build failed"; exit 1; }
export BACKEND_BUILD_DIR="$BUILD"

# the tests' own tools, independent of the build's environment
RUN=(uv run --no-project --quiet --with pytest --with httpx --with ruff --with mypy)
cd "$TESTS" || exit 1

"${RUN[@]}" pytest -q -p no:cacheprovider .
status=$?
[ "$status" -eq 5 ] && { echo "no conformance tests were collected"; exit 1; }
[ "$status" -ne 0 ] && exit "$status"

checks=0
"${RUN[@]}" ruff format --check . || checks=1
"${RUN[@]}" ruff check . || checks=1
"${RUN[@]}" mypy --ignore-missing-imports --explicit-package-bases . || checks=1
[ "$checks" -ne 0 ] && { echo "conformance tests pass; static checks fail"; exit 80; }
exit 0
