---
description: Review what changed in the upstream template since this project's baseline, port the changes the human picks, and advance the baseline (--check: drift notice only; --init: set the baseline).
argument-hint: "[--check | --init [<template-ref>]]"
allowed-tools:
  - Bash
  - Read
  - Edit
  - Write
  - Skill
common_files:
  - docs/TEMPLATE_SYNC.md
  - .claude/template-sync.ini
  - pyproject.toml
suggested_sequence:
  - read the baseline; stop if uninitialized (offer --init)
  - clean tree, cut claude/template-sync-<date> from latest main
  - fetch the template remote, list first-parent units since the baseline
  - classify each unit (category x local state), present the table, stop
  - port the chosen units one commit each; ledger the rest
  - advance the baseline, make check, hand over to /finish-task
---

# /template-sync — pull good changes down from the template

Read `docs/TEMPLATE_SYNC.md` first; it holds the classification rubric
and the exact commands. This file is the order of operations.

The baseline lives in `.claude/template-sync.ini`. The placeholder
package name the template uses is `your_project_name`; this project's
real name is the `name` field in `pyproject.toml`. Every template path
and diff is read through that rename (the doc's `$RENAME`).

## Modes

- **no argument** — the full review below.
- **`--check`** — run `.claude/hooks/template-drift-check.sh --force`,
  relay its one line (or "template baseline is current"), and stop.
- **`--init [<template-ref>]`** — set the baseline once. Add the
  fetch-only `template` remote if missing, fetch it, and propose a
  commit: `<template-ref>` if given; otherwise the template's head for a
  repo whose first commit is less than a day old, and the last
  first-parent template commit before this repo's first commit for an
  older one (command in the doc's "Initializing the baseline"). Show
  the proposed commit with its date and subject and **wait for the
  human to confirm** — a wrong baseline either hides changes or
  re-reviews ported ones. Then write `template.commit` as the **full
  40-hex SHA** (`git rev-parse --verify "<commit>^{commit}"` — never the
  ref name or an abbreviation; the drift check compares it against
  `git ls-remote` output) and `template.syncedAt`, and leave the file
  for the human to commit with
  whatever task they are on (or as `chore(template): set sync baseline`).

## Full review

1. **Read the baseline.** If `.claude/template-sync.ini` is missing,
   say the project has opted out and stop. If `template.commit` is
   empty, stop and offer `--init`. Never guess a baseline.
2. **Preconditions, as for `/start-task`.** `git status` clean (stop
   otherwise — never stash), `git fetch origin --prune`, sync `main`,
   `git checkout -b claude/template-sync-$(date +%F)`. If that branch
   exists, ask whether to resume it.
3. **Fetch the template.** Ensure the fetch-only `template` remote
   (doc: "Initializing the baseline"), then `git fetch template --quiet`.
   If `template.commit` is not an ancestor of `template/<ref>`
   (`git merge-base --is-ancestor`), the template rewrote history or
   the baseline is wrong: stop and report.
4. **List the units.** `git log --first-parent --format='%h %cs %s'
   <baseline>..template/<ref>`. Zero units → say the baseline is
   current, delete the branch, stop. More than 30 units → say so and
   review the oldest 30 (the baseline advances only past the reviewed
   ones, so the rest surface next time).
5. **Classify.** For each unit: files (`git diff --name-status`),
   category per the doc's table, local state per file (clean /
   diverged / pruned / new via the doc's three-way check), and a
   proposal — Adopt, Adapt, Skip — with a one-line why. Split a unit
   whose files fall in different categories. Skipped-ledger entries
   from earlier syncs are not units; the baseline already passed them.
6. **Present the review table** (doc: "The review table") and **stop**.
   Interactive: wait for the human's picks; the proposal column is only
   the default, and "take the defaults" is a valid answer.
   **Autonomous runs stop here for good**: the table is the report, no
   branch is pushed, the baseline does not move.
7. **Port the picks**, one commit per unit in template order, with the
   doc's `git apply --check` → `git apply --index` recipe; when the
   check fails, read the unit's diff and make the equivalent edit by
   hand. Commit as `chore(template): port #<n> <template PR title>` with
   the template commit URL in the body. If a port needs more than the
   files the unit touched (a renamed target, a pruned dependency), say
   so in that commit's body rather than widening silently.
8. **Ledger the rest.** Every unit not adopted gets
   `skipped.<sha7>.title` and `skipped.<sha7>.reason` in the ini (doc:
   "Record the rest"). The reason is one line and specific — `pruned in
   init`, `project locks deps`, `README rewritten` — not "not needed".
9. **Advance the baseline** to the template head you listed in step 4 (not
   beyond), set `template.syncedAt` to today, commit as
   `chore(template): advance baseline to <sha7>`.
10. **`make check`.** Fix or revert the port that broke it; never leave
    a red tree. Then hand over to `/finish-task`: it pushes, opens the
    PR, and runs `/pr-review`. Put the review table in the PR body under
    Key changes, and any "carry back: …" notes (fixes the template
    should take from this project) under Summary.

If any step blocks and the cause is non-obvious — the remote needs
credentials, a unit's diff touches a file the project renamed, the
baseline looks wrong — stop and report before guessing.
