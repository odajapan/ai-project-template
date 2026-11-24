#!/usr/bin/env bash
# One-line "the template has moved" notice. Called from the SessionStart hook
# (throttled to once per TEMPLATE_SYNC_CHECK_DAYS, default 7) and, with
# --force, from the /start-task and /land milestones. Prints nothing unless
# the template's branch is past the baseline in .claude/template-sync.ini —
# so a project that has initialized nothing, or the template repo itself
# (empty template.commit), never hears from it.
#
# Read-only and network-light: one `git ls-remote` (no fetch, no remote
# needed). Never fails the session: every error path exits 0 silently.
# The full review is /template-sync (docs/TEMPLATE_SYNC.md).

set -uo pipefail

force=0
[ "${1:-}" = "--force" ] && force=1

root="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
cfg="$root/.claude/template-sync.ini"
[ -f "$cfg" ] || exit 0

cfg_get() { git config -f "$cfg" "$1" 2>/dev/null || true; }
repo=$(cfg_get template.repo)
ref=$(cfg_get template.ref)
baseline=$(cfg_get template.commit)
synced=$(cfg_get template.syncedAt)
[ -n "$repo" ] && [ -n "$baseline" ] || exit 0
ref=${ref:-main}

# Throttle stamp lives in the shared .git dir, so worktrees share it and it
# is never committed.
gitdir=$(git -C "$root" rev-parse --git-common-dir 2>/dev/null) || exit 0
case "$gitdir" in /*) ;; *) gitdir="$root/$gitdir" ;; esac
stamp="$gitdir/template-sync-last-check"
days="${TEMPLATE_SYNC_CHECK_DAYS:-7}"
if [ "$force" -eq 0 ] && [ -f "$stamp" ]; then
  last=$(cat "$stamp" 2>/dev/null || echo 0)
  now=$(date +%s)
  if [ $((now - last)) -lt $((days * 86400)) ]; then
    exit 0
  fi
fi

# GIT_TERMINAL_PROMPT=0: a private template with no credential helper must
# fail fast, not hang the session start on a password prompt.
head=$(GIT_TERMINAL_PROMPT=0 git ls-remote --quiet "https://github.com/$repo.git" \
  "refs/heads/$ref" 2>/dev/null | cut -f1) || exit 0
[ -n "$head" ] || exit 0
date +%s > "$stamp" 2>/dev/null || true
# Prefix match: ls-remote returns 40 hex chars, but a hand-edited baseline
# may be abbreviated; an exact compare would then report drift forever.
case "$head" in "$baseline"*) exit 0 ;; esac

# A count is only possible once `template` has been fetched (the review
# does that); before then the notice just says "moved".
count=""
if git -C "$root" cat-file -e "$head^{commit}" 2>/dev/null \
   && git -C "$root" cat-file -e "$baseline^{commit}" 2>/dev/null; then
  count=$(git -C "$root" rev-list --count --first-parent "$baseline..$head" 2>/dev/null || true)
fi

printf 'Template drift: %s@%s is past the synced baseline %s%s%s. Run /template-sync to review (one line to the user now; do not start it mid-task).\n' \
  "$repo" "$ref" "${baseline:0:7}" \
  "${synced:+ (synced $synced)}" \
  "${count:+ by $count first-parent commit(s)}"
exit 0
