---
name: new-clone
description: Create a dedicated clone of this repo for a long-lived tmux session (clone + data symlink + .venv + pnpm install + tmux-projects entry). Use only when the user asks for a new clone or tmux session; it writes outside the repo.
argument-hint: <suffix> [session-name]
disable-model-invocation: true
---

# /new-clone — dedicated clone for a long-lived tmux session

Optional tooling for people who boot their tmux sessions from a
tmux-boot-style launcher that reads `<session> <dir>` lines from
`~/.config/tmux-projects`. The launcher itself is personal setup, not part
of this repo.

Use this instead of a git worktree for sessions that must survive reboots:
such a launcher skips a project whose directory is missing, and worktrees
get removed after their PR merges (`/land`, `git worktree prune`). A clone is
not cleaned up by accident.

`$ARGUMENTS` is `<suffix> [session-name]`:

- `<suffix>` — the clone lands in `../<repo>-<suffix>` (e.g. `ui` →
  `../<repo>-ui`, where `<repo>` is the last segment of the origin URL).
- `[session-name]` — tmux session name registered in
  `~/.config/tmux-projects` (default `<repo>-<suffix>`, with characters tmux
  rewrites mapped to `-`).

If `$ARGUMENTS` is empty, ask the user for the suffix; do not guess.

Validate the arguments first: `<suffix>` must match `[A-Za-z0-9._-]+` and
not start with `.`; `[session-name]` must match `[A-Za-z0-9_-]+` and not
start with `-` (tmux rewrites `.`/`:` in names). If they do not, ask the
user instead of running anything — this also rules out shell metacharacters.

Then run it with each argument quoted, by absolute path (the cwd may be a
subdirectory):

```bash
"$(git rev-parse --show-toplevel)/scripts/new_clone.sh" '<suffix>' ['<session-name>']
```

The script is idempotent (re-running skips what exists). It clones from
`origin`, so if the clone fails with an authentication or network error,
stop and report it to the user instead of retrying.

Then report to the user, briefly:

- the clone path and the registered session name;
- that the tmux session is **not** started — the launcher creates it (it
  skips sessions that already exist) or `tmux new -s <session> -c <dir>`;
- if the launcher runs `claude --continue`, there is no conversation to
  resume in a fresh clone — the first launch there should be plain `claude`
  (and the folder-trust prompt is the user's to answer);
- that the clone shares `data/` with the main checkout via a symlink, so
  anything that rewrites `data/` affects both;
- what the script does **not** set up: `.env` and
  `.claude/settings.local.json` are not copied;
- the clone gets its own `.venv` (`make venv`: `python3.12`, the newest
  pyenv 3.12.x if present, or `VENV_PYTHON=/path/to/python`, plus the
  canonical extras), so its editable install points at the clone, not the
  main checkout. Every `make` target uses it without activation; run things
  directly with `.venv/bin/python`. If the output says `make venv failed`,
  or `no venv target` (a checkout from before `make venv` existed), the
  clone has no `.venv`: a shared environment's (conda or venv) editable
  install then points at the **main** checkout's `src/`. `make` targets
  still use the clone's `src/` through the exported `PYTHONPATH` (`make
  which_src` shows what make uses), but `python scripts/x.py` or the CLI run
  directly need `PYTHONPATH=$PWD/src`. Tell the user to run `make venv` in
  the clone; re-running the script also retries it. UI-only work under
  `web/` is unaffected;
- if the output says `pnpm install failed`, the clone is still registered
  and usable — re-running the script retries only the install;
- if the script exits with `session '<name>' is already registered for
  <other dir>`, the clone exists but the session is **not** registered for
  it (typically a stale entry pointing at a removed worktree). Show the user
  the offending line and let them fix or remove it, or pick another session
  name — do not edit `~/.config/tmux-projects` yourself.

This skill deliberately has no `allowed-tools` grant: the script writes
outside the repo (a sibling clone and `~/.config/tmux-projects`), so the
normal Bash approval prompt is the safeguard.

Do not start tmux sessions, kill existing ones, or edit
`~/.config/tmux-projects` by hand.
