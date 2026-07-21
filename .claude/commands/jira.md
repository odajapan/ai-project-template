---
description: Reference for the optional Jira ↔ GitHub workflow (scripts/jira_task.py).
argument-hint: <subcommand> [args...]
allowed-tools:
  - Bash
  - Read
common_files:
  - docs/JIRA_GITHUB_WORKFLOW.md
  - scripts/jira_task.py
suggested_sequence:
  - check ~/.config/jira/env is sourced
  - check repo is initialized (~/.config/jira/repo-epic-map.yaml)
  - run the requested scripts/jira_task.py subcommand
  - report output verbatim
---

# /jira — one Jira issue = one branch = one PR

This is an **optional** workflow, separate from `/start-task` /
`/finish-task` / `/land`. Only use it if this project actually tracks work
in Jira (i.e. `~/.config/jira/repo-epic-map.yaml` has an entry for this
repo, or the user asks to set one up). Full docs:
[docs/JIRA_GITHUB_WORKFLOW.md](../../docs/JIRA_GITHUB_WORKFLOW.md).

`$ARGUMENTS` is the subcommand and its args, forwarded to
`scripts/jira_task.py`. Subcommands:

- `init "Epic Title"` — one-time: create the Epic, map this repo to it
- `new "Summary" --description-file PATH` — create an issue + branch
- `start ABC-NNN` — branch + transition an existing issue
- `pr [--body-file PATH] [--coderabbit]` — push, open PR, link to Jira,
  transition to Review
- `done` — verify the PR merged, transition to Done
- `describe ABC-NNN --description-file PATH` — replace an issue's
  description
- `link-pr [ABC-NNN] [--pr N]` — backfill a PR ↔ issue link
- `status` — show Jira info for the current branch's issue

Steps:

1. If `~/.config/jira/env` doesn't look sourced (no `JIRA_BASE_URL` etc.),
   say so and point at the Setup section of
   [docs/JIRA_GITHUB_WORKFLOW.md](../../docs/JIRA_GITHUB_WORKFLOW.md)
   instead of guessing at credentials.
2. Run `scripts/jira_task.py $ARGUMENTS`.
3. Report the command's output. Every subcommand here that mutates Jira or
   GitHub state (`new`, `start`, `pr`, `done`, `describe`) is a **real,
   externally-visible action** (creates/transitions a Jira issue, pushes a
   branch, opens or comments on a PR) — confirm with the user before
   running one of these unless they explicitly asked for that exact
   subcommand and arguments.
