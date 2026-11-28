#!/usr/bin/env bash
# pre-commit entry point for ruff and mypy: runs `<python> -m <tool> [args]`
# so the hooks judge with the versions `make check` uses, not whatever `ruff`
# or `mypy` happens to be first on PATH. The interpreter, in order:
#   1. $PRECOMMIT_PYTHON          — `make precommit` sets it to make's interpreter
#   2. <checkout>/.venv/bin/python — only once `make venv` finished (marker
#                                   file) and the python still resolves
#   3. python                      — whatever is active (a conda env, a venv)
set -uo pipefail

tool=${1:-}
if [ -z "$tool" ]; then
  echo "usage: scripts/precommit_tool.sh <tool> [args...]" >&2
  exit 2
fi
shift

root=$(cd "$(dirname "$0")/.." && pwd -P)
if [ -n "${PRECOMMIT_PYTHON:-}" ]; then
  py=$PRECOMMIT_PYTHON
elif [ -f "$root/.venv/.make-venv-ok" ] && [ -x "$root/.venv/bin/python" ]; then
  py=$root/.venv/bin/python
else
  py=python
fi

if ! command -v "$py" >/dev/null 2>&1; then
  echo "precommit_tool.sh: interpreter '$py' not found" >&2
  exit 1
fi
if ! "$py" -c "import importlib.util, sys; sys.exit(importlib.util.find_spec('$tool') is None)" 2>/dev/null; then
  echo "precommit_tool.sh: '$tool' is not installed for $py; run make venv" >&2
  exit 1
fi
exec "$py" -m "$tool" "$@"
