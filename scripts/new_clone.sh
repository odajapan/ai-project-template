#!/usr/bin/env bash

set -euo pipefail

## Create a dedicated clone of this repo for a long-lived tmux session
## (e.g. a UI session that runs alongside the main checkout).
##
## Optional tooling: it is for people who boot their tmux sessions from a
## tmux-boot-style launcher that reads "<session> <dir>" lines from
## ~/.config/tmux-projects (the launcher itself is personal setup, not part of
## this repo). Why a clone and not a git worktree: such a launcher skips any
## project whose directory is missing, and worktrees get removed after a PR
## merges (/land, `git worktree prune`) -- which silently stopped the session
## from coming back after a reboot. A clone is never cleaned up by accident.
##
## Usage:
##   scripts/new_clone.sh <suffix> [session-name]
##
##   scripts/new_clone.sh ui              # ../<repo>-ui, session <repo>-ui
##   scripts/new_clone.sh ui my-UI        # same directory, session named my-UI
##
## Idempotent: re-running skips whatever already exists.
##
## Steps: clone origin -> symlink the main checkout's data/ when data/ is
## gitignored as a whole (a tracked data/ skeleton, as the template ships, is
## left as cloned) -> register the session in ~/.config/tmux-projects (override the
## path with TMUX_PROJECTS) so the launcher recreates it after a reboot ->
## `make venv` (the clone's own .venv, so its editable install points at the
## clone, not the main checkout) -> pnpm install in web/ if it exists.
## The session itself is not started; run your launcher or
## `tmux new -s <session> -c <dir>` for that.

TMUX_PROJECTS="${TMUX_PROJECTS:-$HOME/.config/tmux-projects}"

if [ $# -lt 1 ] || [ $# -gt 2 ]; then
  echo "usage: $0 <suffix> [session-name]" >&2
  exit 2
fi

SUFFIX="$1"

## The suffix becomes a sibling directory name and the session a
## whitespace-separated field that the launcher parses with `read` and passes
## to `tmux -t`, so reject anything that would escape the parent dir, split or
## comment out the line, or be rewritten by tmux.
case "$SUFFIX" in
  '' | .* | *[!A-Za-z0-9._-]*)
    echo "error: suffix must match [A-Za-z0-9._-]+ and not start with '.'" >&2
    exit 2
    ;;
esac

## Resolve from the script's own dir so the caller's cwd does not matter.
## --git-common-dir is the main checkout's .git when run from a worktree, but
## from a dedicated clone it is that clone's own .git; so take the repo name
## from the origin URL (not the directory name) to keep new clones named
## <repo>-<suffix> regardless of where the script was started.
cd "$(dirname "${BASH_SOURCE[0]}")"
MAIN_REPO="$(cd "$(git rev-parse --git-common-dir)/.." && pwd)"
ORIGIN_URL="$(git -C "$MAIN_REPO" remote get-url origin)"
## Last path segment, also for scp-style (git@host:repo.git) and trailing-slash URLs.
REPO_NAME="${ORIGIN_URL%/}"
REPO_NAME="${REPO_NAME%.git}"
REPO_NAME="${REPO_NAME##*[/:]}"
TARGET="$(dirname "$MAIN_REPO")/$REPO_NAME-$SUFFIX"

## tmux rewrites '.' and ':' in session names and reads a leading '-' as an
## option, so the default name maps every other character to '-'.
SESSION="${2:-${REPO_NAME//[^A-Za-z0-9_-]/-}-${SUFFIX//./-}}"
case "$SESSION" in
  '' | -* | *[!A-Za-z0-9_-]*)
    echo "error: session name must match [A-Za-z0-9_-]+ and not start with '-'" >&2
    exit 2
    ;;
esac

## The launcher splits each line with `read -r name dir rest` and expands ~, so
## a path with whitespace, '#', '$' etc. would be mis-read or truncated.
case "$TARGET" in
  '' | *[!A-Za-z0-9._/+@-]*)
    echo "error: $TARGET has characters a tmux-projects launcher cannot read (allowed: A-Za-z0-9._/+@-)" >&2
    exit 1
    ;;
esac

if [ -d "$TARGET/.git" ]; then
  if ! git -C "$TARGET" rev-parse --verify -q HEAD >/dev/null; then
    echo "error: $TARGET has a .git but no valid HEAD (interrupted clone?); move it away and re-run" >&2
    exit 1
  fi
  echo "clone: $TARGET already exists, skipping"
elif [ -e "$TARGET" ]; then
  echo "error: $TARGET exists but is not a git clone; move it away and re-run" >&2
  exit 1
else
  ## From $MAIN_REPO so a relative/local-path origin resolves like it did
  ## for the main checkout (the script itself runs from scripts/).
  (cd "$MAIN_REPO" && git clone "$ORIGIN_URL" "$TARGET")
fi

## data/ is usually a gitignored (often multi-GB) snapshot; share the main
## checkout's copy. A project that still tracks the data/ skeleton (the
## template ships data/*/.gitkeep) gets a real data/ from the clone itself;
## that is left alone, since replacing tracked files with a symlink would show
## up as deletions in `git status`.
if [ -L "$TARGET/data" ]; then
  echo "data: $TARGET/data already linked, skipping"
elif [ -e "$TARGET/data" ]; then
  echo "data: $TARGET/data is part of the clone (data/ is not fully gitignored), not linking"
elif [ -d "$MAIN_REPO/data" ]; then
  ## -P resolves a symlinked data/ (when started from another clone) to the
  ## real directory so links never chain through a clone that may be deleted.
  DATA_SRC="$(cd -P "$MAIN_REPO/data" && pwd)"
  ln -s "$DATA_SRC" "$TARGET/data"
  echo "data: linked to $DATA_SRC"
else
  echo "data: $MAIN_REPO/data not found, skipping" >&2
fi
## The trailing-slash gitignore pattern does not match a symlink, so exclude
## it locally to keep `git status` clean.
if [ -L "$TARGET/data" ]; then
  mkdir -p "$TARGET/.git/info"
  if ! grep -qxF '/data' "$TARGET/.git/info/exclude" 2>/dev/null; then
    echo '/data' >> "$TARGET/.git/info/exclude"
  fi
fi

## Register before the slow, fallible installs so a failure there does not
## leave the clone unregistered.
## The launcher reads "<session> <dir>" lines and expands ~ itself.
## A session is "taken" if its name OR its directory is already listed
## (session names are case-sensitive, so `<repo>-ui` and `<repo>-UI` would
## otherwise both start in the same clone).
## Abbreviate only at a path boundary: /Users/hoda2/x must not become ~2/x.
DISPLAY_DIR="$TARGET"
case "$TARGET" in
  "$HOME"/*) DISPLAY_DIR="~${TARGET#"$HOME"}" ;;
esac
mkdir -p "$(dirname "$TMUX_PROJECTS")"
OWNER=""
if [ -f "$TMUX_PROJECTS" ]; then
  ## ENVIRON (not -v) so backslashes in paths are not treated as escapes, and
  ## no sub() so '&' in $HOME is not a replacement metacharacter.
  OWNER="$(SESSION="$SESSION" TARGET="$TARGET" awk '
    /^[[:space:]]*(#|$)/ { next }
    {
      dir = $2
      if (substr(dir, 1, 1) == "~") dir = ENVIRON["HOME"] substr(dir, 2)
      sub(/\/+$/, "", dir)
    }
    $1 == ENVIRON["SESSION"] || dir == ENVIRON["TARGET"] { print $1 "\t" dir; exit }
  ' "$TMUX_PROJECTS")"
fi
if [ -n "$OWNER" ]; then
  OWNER_NAME="${OWNER%%$'\t'*}"
  OWNER_DIR="${OWNER#*$'\t'}"
  if [ "$OWNER_DIR" = "$TARGET" ]; then
    echo "tmux-projects: '$OWNER_NAME' already registered for $DISPLAY_DIR, leaving it as is"
    SESSION="$OWNER_NAME"
  else
    ## The case this script exists for: a stale entry (e.g. a pruned worktree)
    ## under the same name. The launcher would skip it and never start the clone.
    echo "error: session '$OWNER_NAME' is already registered for $OWNER_DIR, not this clone ($DISPLAY_DIR)." >&2
    echo "       Fix or remove that line in $TMUX_PROJECTS, or pick another session name; the clone itself is ready." >&2
    exit 1
  fi
else
  ## A hand-edited file may lack a trailing newline; do not glue onto its last line.
  if [ -s "$TMUX_PROJECTS" ] && [ -n "$(tail -c1 "$TMUX_PROJECTS")" ]; then
    echo >> "$TMUX_PROJECTS"
  fi
  printf '%s %s\n' "$SESSION" "$DISPLAY_DIR" >> "$TMUX_PROJECTS"
  echo "tmux-projects: registered '$SESSION' -> $DISPLAY_DIR"
fi

## Non-fatal like pnpm below: re-running retries only the missing pieces. pip's
## output is shown only on failure (it is a page of "already satisfied" on a re-run).
if ! grep -q '^venv:' "$TARGET/Makefile" 2>/dev/null; then
  echo "venv: $TARGET/Makefile has no venv target (older checkout?), skipping" >&2
elif ! command -v make >/dev/null 2>&1; then
  echo "venv: make not found, skipping" >&2
elif VENV_LOG="$(make -s -C "$TARGET" venv 2>&1)"; then
  echo "venv: $TARGET/.venv ready"
else
  printf '%s\n' "$VENV_LOG" | tail -n 15 >&2
  echo "venv: make venv failed; the clone is registered, re-run this script (or make venv in the clone) to retry" >&2
fi

if [ -f "$TARGET/web/package.json" ]; then
  if command -v pnpm >/dev/null 2>&1; then
    ## Non-fatal: the clone, data link and registration are already done, and
    ## the install can fail for registry, TLS or network reasons.
    (cd "$TARGET/web" && pnpm install --frozen-lockfile) ||
      echo "web: pnpm install failed; the clone is usable, re-run this script to retry" >&2
  else
    echo "web: pnpm not found, skipping install" >&2
  fi
fi

echo "done: $TARGET (session: $SESSION)"
