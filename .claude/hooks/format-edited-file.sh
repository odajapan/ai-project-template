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

# python3 is a hard requirement of this project, so it is the primary JSON
# reader; jq is only a fallback (macOS does not ship it).
if command -v python3 >/dev/null 2>&1; then
  file=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input", {}).get("file_path", ""))' 2>/dev/null)
elif command -v jq >/dev/null 2>&1; then
  file=$(jq -r '.tool_input.file_path // empty' 2>/dev/null)
else
  exit 0
fi

case "$file" in
  *.py) ;;
  *) exit 0 ;;
esac

[ -f "$file" ] || exit 0

# Only files under this project are formatted: a session can edit a file in
# another repo or a scratch directory, and that project's formatter settings
# are not ours. Both sides are compared as physical paths (`pwd -P`) so a
# worktree, a symlinked checkout, or macOS's /tmp -> /private/tmp still
# compares equal instead of silently skipping real edits.
root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
real_root=$(cd "$root" 2>/dev/null && pwd -P) || exit 0
real_file=$(cd "$(dirname "$file")" 2>/dev/null && pwd -P)/$(basename "$file") || exit 0

case "$real_file" in
  "$real_root"/.claude/worktrees/*/*)
    # A worktree under .claude/worktrees/ is a separate checkout with its own
    # .venv; format with that checkout's ruff, not the main checkout's.
    rest=${real_file#"$real_root"/.claude/worktrees/}
    real_root="$real_root/.claude/worktrees/${rest%%/*}"
    ;;
  "$real_root"/*) ;;
  *) exit 0 ;;
esac

# Prefer the project's ruff so the hook agrees with `make check` and
# pre-commit even when the venv is not activated in the launching shell.
if [ -x "$real_root/.venv/bin/ruff" ]; then
  ruff="$real_root/.venv/bin/ruff"
elif command -v ruff >/dev/null 2>&1; then
  ruff="ruff"
else
  exit 0
fi

# --force-exclude: an explicitly passed path bypasses pyproject's `exclude`
# otherwise, so a generated or vendored file would get reformatted.
"$ruff" format --quiet --force-exclude "$real_file" >/dev/null 2>&1 || true
exit 0
