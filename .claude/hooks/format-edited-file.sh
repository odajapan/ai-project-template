#!/usr/bin/env bash
# PostToolUse(Edit|Write) hook: ruff-format only the file that was just edited.
#
# Reads the hook payload from stdin and formats `tool_input.file_path`. Scoped to
# one file on purpose: the old `make format` run touched every file under src/,
# tests/ and scripts/, so a fix could rewrite files the task never changed, and
# its `ruff check --fix` deleted a just-added import as "unused" whenever the
# first usage landed in a later Edit. Formatting alone has no such race; lint
# fixes stay in `make format` / `make check`, run deliberately.
#
# Never fails the tool call: the hook is a convenience, not a gate.

set -uo pipefail

if ! command -v jq >/dev/null 2>&1; then
  exit 0
fi

file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)

case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
case "$file" in
  "$root"/src/*|"$root"/tests/*|"$root"/scripts/*) ;;
  *) exit 0 ;;
esac

# Prefer the project's ruff so the hook agrees with `make check` and
# pre-commit even when the venv is not activated in the launching shell.
if [ -x "$root/.venv/bin/ruff" ]; then
  ruff="$root/.venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
  ruff="ruff"
else
  exit 0
fi

"$ruff" format --quiet "$file" >/dev/null 2>&1 || true
exit 0
