# Jira ↔ GitHub workflow (optional)

This is an **optional, additive** workflow for projects that track work in
Jira. It coexists with the template's default `/start-task` /
`/finish-task` / `/land` flow ([.claude/commands/](../.claude/commands/)) —
use whichever matches how the project actually tracks work. If there's no
Jira project, ignore this document entirely; nothing here is wired into
`make check` or CI.

We treat each unit of work as **one Jira issue, one branch, one PR**. The
plumbing lives in [`scripts/jira_task.py`](../scripts/jira_task.py); this
document is its manual.

Nothing in the tool is tied to a specific organization, Jira project, or
workflow: status transitions are resolved by **name** at call time (via the
Jira REST API), not hard-coded numeric IDs, and the org-specific bits — base
URL, project key, base branch, branch prefix, status names — all live in a
per-machine config file, never in this repo.

## Setup (one-time)

1. **Generate a Jira API token** at
   https://id.atlassian.com/manage-profile/security/api-tokens .
2. **Store credentials** in a 600-permission env file:
   ```bash
   mkdir -p ~/.config/jira && chmod 700 ~/.config/jira
   touch ~/.config/jira/env && chmod 600 ~/.config/jira/env
   nano ~/.config/jira/env
   ```
   Contents (replace every value with your own — do not commit real
   credentials):
   ```bash
   export JIRA_BASE_URL="https://<your-domain>.atlassian.net"
   export JIRA_EMAIL="<your-atlassian-email>"
   export JIRA_API_TOKEN="<token from step 1>"
   export JIRA_PROJECT_KEY="<YOUR_PROJECT_KEY>"
   ```
3. **Auto-source on shell start** — append to your shell rc file
   (`~/.zshrc` / `~/.bashrc`):
   ```bash
   [ -f "$HOME/.config/jira/env" ] && source "$HOME/.config/jira/env"
   ```
4. **Verify**:
   ```bash
   source ~/.zshrc   # or open a new terminal
   curl -s -o /dev/null -w "HTTP %{http_code}\n" -u "$JIRA_EMAIL:$JIRA_API_TOKEN" "$JIRA_BASE_URL/rest/api/3/myself"   # expect: HTTP 200
   ```
5. **Bootstrap this repo** (one Epic per repo):
   ```bash
   scripts/jira_task.py init "Your Epic Title"
   ```
   This creates the Epic in Jira and writes a mapping into
   `~/.config/jira/repo-epic-map.yaml`, keyed by the repo directory's
   basename:
   ```yaml
   repos:
     <repo-dir-name>:
       epic: ABC-123
       base_branch: main
       branch_prefix: feature       # -> feature/ABC-123-slug
       default_labels: []
       statuses:                    # target status NAMES, resolved via API
         in_progress: In Progress
         review: In Review
         done: Done
   ```
   If your Jira project's workflow uses different status names than the
   three defaults above (e.g. "In Dev" instead of "In Progress"), edit the
   `statuses` block after `init` — `jira_task.py` looks up the matching
   transition ID from the issue's own available transitions at call time,
   so it never needs the numeric IDs your Jira admin configured.

## Command reference

All commands assume CWD is somewhere inside the repo. Credentials are read
from `~/.config/jira/env`.

### `new "Summary"`

Creates a Task under the repo's Epic, transitions it to the configured
`in_progress` status, branches off `main` (or whatever `base_branch` the
repo map specifies), and posts a "branch created" comment on the issue.

```bash
scripts/jira_task.py new "Fix /metrics/records pagination" \
  --description-file /tmp/desc.md \
  --label tech-debt --label api
```

Flags:
- `--type {Task,Story}` — default `Task`
- `--label LABEL` — repeatable; merged with `default_labels` from the repo
  map
- `--description "..."` / `--description-file PATH` / `--description-stdin`
  — **required**: the command hard-exits with an error if none of these is
  provided. See the description template below.
- `--backlog` — prefill mode: create the issue in **Backlog** without
  creating a local branch or transitioning status. Use `start <KEY>` later
  to actually begin work. Useful for bulk-seeding planned work into Jira
  ahead of time so it's visible / pickable from the board.
- `--force` — bypass the dedup guard. By default, `new` refuses to create
  an issue when an existing open issue under the Epic has the same summary
  (it points at the existing key and suggests `start <KEY>`). Use this only
  when you genuinely want two issues with the same title.

### `start ABC-NNN`

Like `new`, but for an existing issue. Transitions to the `in_progress`
status, branches off the configured `base_branch`, comments.

### `pr [--title T] [--body / --body-file / --body-stdin] [--coderabbit]`

Pushes the current branch, creates a PR with
`gh pr create --base <base_branch>` (defaults to `main` per the repo map),
attaches the PR as a **Remote Link** on the Jira issue, and transitions the
issue to the configured `review` status.

```bash
scripts/jira_task.py pr --body-file /tmp/pr_body.md
```

Flags:
- `--title T` — default is `<KEY>: <issue summary>` pulled from Jira
- `--coderabbit` — trigger `@coderabbitai full review` on the new PR. Off
  by default; only useful if this repo has
  [CodeRabbit](https://www.coderabbit.ai/) installed.
- If a PR for the branch already exists, the script skips creation and just
  updates the link / transitions.

### `done [ABC-NNN] [--force]`

Run after the PR is merged. Transitions the issue to the configured `done`
status, marks the Remote Link `resolved`, and appends a "Merged in PR #N
(commit XXXXXXXX)" comment.

```bash
scripts/jira_task.py done
```

Merge verification: the PR-merged check only fires when the script can
resolve a PR for the current branch *and* the branch's issue key matches
the issue you're transitioning (typically: you're sitting on the
corresponding `<prefix>/ABC-NNN-*` branch). Running `done ABC-NNN` from any
other branch (e.g. `main` or a different `<prefix>/*`) skips the
verification and exits unless `--force` is passed. Switch to the matching
branch before running `done`, or use `--force` when the branch is no
longer available (e.g. it was deleted after merge).

### `describe ABC-NNN`

Replace the description of an existing issue. Use this on status
transitions (especially when moving to Review or Done) to record what's
actually shipping.

```bash
scripts/jira_task.py describe ABC-287 --description-file /tmp/updated_desc.md
```

### `link-pr [ABC-NNN] [--pr N]`

Standalone Remote Link upsert — useful for backfilling. Idempotent:
re-running with the same PR updates the existing link.

### `status`

Print Jira info (type, summary, status, parent Epic, labels) for the issue
inferred from the current branch name.

## Description template

Use this skeleton when writing the `--description` body. Paragraphs are
split on blank lines; single newlines inside a paragraph become hard
breaks. ADF does not render Markdown, so don't bother with `**bold**` —
just plain prose.

```text
Problem

What was broken / why this work exists. Reference the file/line where the issue
lives so the ticket is searchable.

Fix

What changed (or, before implementation, the plan). Mention follow-ups if any.

Why it matters

The user-facing impact. Lets a reviewer rank priority without reading the diff.

Acceptance criteria

- Concrete pass/fail items
- One per line
- Including test coverage if relevant

Status / links

Branch: <prefix>/ABC-NNN-short-slug (off main)
PR: https://github.com/.../pull/N
Follow-up: what still needs to happen after merge (data refresh, deploy, etc.)
```

Update the description when transitioning to Review (add PR link / change
summary) and to Done (add merge commit, mark follow-ups as done or carved
out into new tickets).

## Typical end-to-end flow

```bash
# 1. Start the work
scripts/jira_task.py new "Fix specs.csv cache invalidation" \
    --label tech-debt --label data-pipeline \
    --description-file /tmp/desc.md

# 2. Implement, commit
git add ...
git commit -m "..."

# 3. Open the PR (also: link + transition to Review)
scripts/jira_task.py pr --body-file /tmp/pr_body.md

# 4. After review and merge:
scripts/jira_task.py done
```

## Daily report

`scripts/daily_report.py` (and the `/daily-report` Claude skill) lists
Jira tickets resolved on a given day under this repo's Epic:

```bash
scripts/daily_report.sh                    # today
scripts/daily_report.sh --date 2026-06-25
```

## Troubleshooting

- **`Missing required env vars`** — `~/.config/jira/env` not sourced.
  `source ~/.zshrc` or open a new terminal.
- **`Repo 'XXX' is not initialized.`** — Run
  `scripts/jira_task.py init "Epic Title"` in the repo root. The mapping is
  keyed by `git rev-parse --show-toplevel`'s basename.
- **`No Jira issue key found in branch name 'XXX'`** — Branch must contain
  a key matching `[A-Z][A-Z0-9]+-\d+` (e.g. `ABC-123`). If you branched
  manually, rename with `git branch -m <prefix>/ABC-NNN-...` then push.
- **PR already exists** — `pr` is idempotent; it skips creation, just
  re-links and re-transitions.
- **`No transition to status 'X' is available`** — The `statuses` mapping
  in `~/.config/jira/repo-epic-map.yaml` doesn't match this Jira project's
  actual workflow status names. The error message lists the statuses that
  *are* reachable from the issue's current state — update the mapping to
  match.

## Reusing this in other repos

`scripts/jira_task.py` auto-detects the current repo from
`git rev-parse --show-toplevel` and looks itself up in the shared
`~/.config/jira/repo-epic-map.yaml`, so the same script works unmodified
across every repo that vendors it from this template. To use it from a
repo that doesn't have its own copy:

```bash
mkdir -p ~/bin
ln -s "$PWD/scripts/jira_task.py" ~/bin/jira-task
# ensure ~/bin is on PATH (add 'export PATH=$HOME/bin:$PATH' to your shell rc if needed)
```

Then in any other repo: `jira-task init "<Epic Title>"` to add it to
`~/.config/jira/repo-epic-map.yaml`, and use the same subcommands.

## Relationship to `/start-task` / `/finish-task`

The template's default flow (`/start-task`, `/finish-task`, `/land`) cuts
`claude/<task-name>` branches and doesn't touch any issue tracker. This
Jira flow is an alternative for projects where work is tracked as Jira
issues under an Epic — pick one flow per project, don't mix branch
conventions. If you adopt this flow, the git-hook branch guards in
[`.githooks/`](../.githooks/) (enabled via `make hooks`) already block
direct commits/pushes to `main`/`master` regardless of which flow created
the feature branch.
