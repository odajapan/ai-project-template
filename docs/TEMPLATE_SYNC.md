# Keeping up with the template

A project created from this template keeps none of the template's git
history ("Use this template" squashes it into one commit), so nothing
tells it when the template fixes a gate, tightens a guardrail, or encodes
a lesson another downstream project learned the hard way. This document
is the procedure for finding those changes and deciding, one template PR
at a time, whether this project wants them.

Driven by `/template-sync` in Claude Code, or by hand following the steps
below. Any agent can follow it; only the drift notice is Claude-specific.

## The pieces

| Piece | Purpose |
|---|---|
| `.claude/template-sync.ini` | The **baseline**: which template commit this project has reviewed up to, plus a ledger of PRs it deliberately skipped and a map of files this project moved (`[path "<template path>"] local = <local path>`). git-config syntax (`git config -f .claude/template-sync.ini template.commit`). Committed, so the whole team shares one baseline. |
| `.claude/hooks/template-drift-check.sh` | The **notice**: one `git ls-remote`, one line of output, only when the template's branch is past the baseline. Runs from the `SessionStart` hook (throttled to once a week; the throttle stamps the attempt, so an unreachable GitHub costs one try per week, not one per session) and from the `/start-task` and `/land` milestones (`--force`). Silent while `template.commit` is empty. |
| `/template-sync` | The **review**: fetch the template, list its merged PRs since the baseline, classify each, port the ones the human picks, advance the baseline. |

## When it runs

- **Periodically, on its own:** the drift notice at session start, task
  start (`/start-task`), and after a merge (`/land`). It only ever says
  "the template has moved, run `/template-sync`" — it never starts a sync,
  and never mid-task. A sync is a task of its own, on its own branch.
- **Explicitly:** `/template-sync` (full review), `/template-sync --check`
  (notice only, ignoring the throttle), `/template-sync --init [<ref>]`
  (set the baseline the first time).

## Initializing the baseline

Once per project. `/init-from-template` does it in Phase 0 for a fresh
clone; a project that predates this procedure does it by hand:

```bash
git remote add template https://github.com/odajapan/ai-project-template.git
git remote set-url --push template no_push
git fetch template --quiet
ref=$(git config -f .claude/template-sync.ini template.ref); : "${ref:=main}"
```

`template.ref` is the template branch the review follows; the ini ships
it as `main`, which is this template's default branch. A template with a
different default branch shows it in
`git remote show template | sed -n 's/.*HEAD branch: //p'` — set
`template.ref` to that first, so the drift check and the review look at
the same branch.

Then **one** of the two, not both — the value is always a full 40-hex SHA
(`rev-parse`), never a ref name or abbreviation:

```bash
# (a) A fresh clone: the template's current head.
baseline=$(git rev-parse --verify "template/$ref^{commit}")
```

```bash
# (b) An older project: the last template commit before this repo's first
# commit — everything after it is genuinely unreviewed. Look at the
# candidate first; if the project already ported later template changes
# by hand, pick a later commit from `git log --first-parent template/$ref`.
first=$(git log --reverse --format=%cI | head -1)
git log "template/$ref" --first-parent --before="$first" -1 --format='%H %cs %s'
baseline=$(git log "template/$ref" --first-parent --before="$first" -1 --format=%H)
```

```bash
git config -f .claude/template-sync.ini template.commit "$baseline"
git config -f .claude/template-sync.ini template.syncedAt "$(date +%F)"
```

Commit the file. If this project never wants template reviews, delete
`.claude/template-sync.ini` instead: the notice and the consistency test
both treat a missing file as an opt-out.

## The review, step by step

1. **Clean tree, own branch.** The review itself is read-only, but
   adoption edits files: cut `claude/template-sync-<YYYY-MM-DD>` from
   latest `main` first (the usual `/start-task` preconditions).
2. **Fetch the template.** Fetch-only remote named `template`
   (the commands above). `git fetch template --quiet`.
3. **List the units.** One unit = one template PR = one first-parent
   commit on the template's branch (the template merges with merge
   commits, so `--first-parent` is exactly the PR list):
   ```bash
   base=$(git config -f .claude/template-sync.ini template.commit)
   ref=$(git config -f .claude/template-sync.ini template.ref); : "${ref:=main}"
   git log --first-parent --format='%h %cs %s' "$base..template/$ref"
   ```
   For each unit, its diff is `git diff "$m^1" "$m"` and its files
   `git diff --name-status "$m^1" "$m"`. A unit that is a plain commit
   (no merge) is reviewed the same way. Review at most 30 units per
   sync, oldest first; `reviewed_head` below is the newest unit you
   actually reviewed — the branch tip only when nothing was cut off:
   ```bash
   reviewed_head=$(git rev-list --first-parent --reverse "$base..template/$ref" | sed -n 30p)
   : "${reviewed_head:=$(git rev-parse "template/$ref")}"
   ```
4. **Map the names.** The template's placeholder package is
   `your_project_name`; this project renamed it (the `name` field in
   `pyproject.toml`, and `src/<name>/`). Every template path and diff is
   read through that mapping:
   ```bash
   pkg=$(sed -n 's/^name = "\(.*\)"/\1/p' pyproject.toml | head -1)
   RENAME="s/your_project_name/${pkg}/g"
   ```
   Files this project **moved or renamed** are a second mapping, kept in
   the ini so every sync sees it — one entry per file (the template
   ships none; `/init-from-template` renames nothing):
   ```ini
   [path "docs/EXAMPLE.md"]
   	local = docs/guides/example.md
   ```
   `local_path` turns a template path into where this project keeps the
   file, both mappings applied; every step below goes through it:
   ```bash
   local_path() {
     local p
     p=$(git config -f .claude/template-sync.ini "path.$1.local") || p=$1
     printf '%s\n' "$p" | sed "$RENAME"
   }
   ```
   Without the map, a unit that touches a moved file is misclassified —
   **new** (nothing at the template path) or **diverged** against the
   wrong file — and `git apply` would then plant a second copy at the
   template's path.
5. **Classify each unit** by the files it touches and by the local
   state of those files. Local state is a three-way question — has this
   project changed the file since the template version the unit starts
   from?
   ```bash
   local=$(local_path "$f")
   git show "$m^1:$f" | sed "$RENAME" | diff -q - "$local"
   ```
   identical → **clean** (the template patch applies as-is);
   differs → **diverged** (port by hand, guided by the diff);
   `$local` missing → **pruned** (removed in `/init-from-template`
   Phase 1, or never adopted — check the `[path]` map before concluding
   that);
   missing at `$m^1` → **new** (the template added it).
6. **Propose, then wait.** Present the table below and stop. The human
   picks; the proposal column is only the default. An autonomous run
   (`--dangerously-skip-permissions`) stops here with the table as its
   report — it never adopts or advances the baseline on its own.
7. **Port the chosen units,** one commit per unit, in template order.
   `port_diff` is one file's slice of the unit with its header pointed
   at the local path, so a moved file receives the patch where it lives:
   ```bash
   port_diff() {
     local f=$1 l; l=$(local_path "$1")
     git diff "$m^1" "$m" -- "$f" | sed "$RENAME" \
       | sed -e "s#^diff --git a/.* b/.*#diff --git a/$l b/$l#" \
             -e "s#^--- a/.*#--- a/$l#" -e "s#^+++ b/.*#+++ b/$l#"
   }
   for f in $files; do
     port_diff "$f" | git apply --check && port_diff "$f" | git apply --index
   done
   ```
   When `--check` fails (the file diverged), read the unit's diff and
   make the equivalent edit by hand — the intent, not the bytes. Commit
   as `chore(template): port #<n> <template PR title>` with the template
   commit URL in the body, so `git log` answers "where did this come
   from" and the next sync can see what was already taken.
8. **Record the rest.** Every unit *not* adopted gets a ledger entry:
   ```bash
   git config -f .claude/template-sync.ini "skipped.$sha7.title" "<title>"
   git config -f .claude/template-sync.ini "skipped.$sha7.reason" "<one line>"
   ```
9. **Advance the baseline** to `reviewed_head` from the listing step,
   whatever was adopted — the baseline means "reviewed up to", not
   "identical to", and never past a unit nobody looked at:
   ```bash
   git config -f .claude/template-sync.ini template.commit "$reviewed_head"
   git config -f .claude/template-sync.ini template.syncedAt "$(date +%F)"
   ```
   Commit as `chore(template): advance baseline to <sha7>`.
10. **`make check`, then `/finish-task`.** A sync is a PR like any other;
    the port commits and the ledger are what the reviewer reads.

### The review table

```
## Template review — <repo>@<ref>: <base7>..<head7> (<n> units)

| # | Template PR | Category | Files (local state) | Proposal | Why |
|---|-------------|----------|---------------------|----------|-----|
| 1 | #83 docs(commands): port three /pr-review refinements | harness | .claude/commands/pr-review.md (diverged) | Adapt | project edited the same section; port by hand |
| 2 | #82 chore(deps): anthropic >=2.8.0 | deps | pyproject.toml (diverged) | Skip | project pins via uv.lock |

Reply with the unit numbers to adopt / adapt / skip (default = Proposal).
```

## What counts as a change worth taking

Adopt a template change when it does one of these for a file this
project still runs:

- **fixes a bug or a gap** in a gate, hook, workflow, or scaffold file;
- **tightens a guardrail** — a deny rule, a consistency test, a
  pre-commit hook, a branch-protection note;
- **encodes a lesson** (a *learning edge*: a reviewer finding that became
  a rule or a test) this project would otherwise relearn on its own.

Leave it when it is wording-only in a doc this project rewrote,
one-shot template tooling already run here, or a subsystem this project
pruned. "Looks nice" is not a reason; "we hit this too" is.

### Category → default proposal

| Category | Template paths | Default |
|---|---|---|
| **harness** | `.claude/**` (not this file's own baseline), `AGENTS.md`, `CLAUDE.md`, `.githooks/` | **Adopt** if clean, **Adapt** if diverged. These files change behaviour of every session. |
| **gate** | `Makefile`, `.github/workflows/ci.yml`, `.pre-commit-config.yaml`, `[tool.*]` in `pyproject.toml`, `tests/test_repo_consistency.py` | **Adopt** / **Adapt**. Keep `make check` and CI identical in spirit, even when the project's extras differ. |
| **deps** | dependency floors in `pyproject.toml`, dependabot bumps | **Skip** when the project locks its own versions (`uv.lock`) or pins differently; otherwise **Adapt** (bump the floor, run `make check`). |
| **scaffold** | `src/your_project_name/**`, `examples/`, `tests/test_llm.py`, `tests/test_cli.py` | **Skip** — the project owns this code now — unless the local file is *clean*, in which case the change is a bug fix the project never looked at: **Adopt**. |
| **docs** | `docs/**`, `README.md` | **Adapt** only for a doc the project still carries unchanged in that section; `README.md` is **Skip**. |
| **pruned** | anything removed in `/init-from-template` Phase 1 (Jira, deploy, data pipeline, web, LLM layer) | **Skip**, reason `pruned in init`. Do not re-add a subsystem through a sync. |
| **template-only** | `docs/TEMPLATE_INIT.md`, `scripts/rename_project.sh`, `.claude/commands/init-from-template.md`, `.github/CODEOWNERS`, `.github/dependabot.yml` | **Skip** — one-shot tooling already run, or settings that are per-repo by nature. |

A unit that spans categories is split in the proposal (adopt the gate
part, skip the scaffold part) — porting is per file, so that is free.

## Going the other way

A fix this project makes to a harness file is often a fix the template
wants too. Note it in the sync PR body ("carry back: …"); the template
maintainer ports it upstream the same way, with the template's own
`/start-task`. Nothing here automates that direction.
