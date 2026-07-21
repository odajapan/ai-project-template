---
description: Verify checks, push the claude/* branch, and open a PR.
allowed-tools:
  - Bash
  - Read
common_files:
  - .github/pull_request_template.md
  - CLAUDE.md
suggested_sequence:
  - verify no forbidden files in git status
  - confirm on claude/* branch
  - run make check
  - commit uncommitted changes with conventional commits
  - git push origin <branch>
  - gh pr create with PR template
  - report PR URL and stop
  - suggest /clear with handoff after merge
---

# /finish-task — wrap up an autonomous task

Run only after `/start-task` and the actual work are complete.

Steps:

1. `git status` — confirm there are no unintended files (data/raw/,
   .env, models/, generated artifacts). Abort and report if there are.
2. `git branch --show-current` — confirm we are on a `claude/*`
   branch. Refuse to continue on `main` / `master`.
3. Run `make check`. If it fails, fix the cause (or report it) and
   re-run before continuing. **Never** push a red branch.
4. Review unstaged / staged changes (`git diff`, `git diff --staged`).
   If anything is still uncommitted, group it into logical commits
   using Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`,
   `test:`, `refactor:`). Do not create a single bulk commit.
5. `git push origin <current-branch>`. If the push is rejected,
   investigate — do NOT use `--force` or `--force-with-lease`.
6. Open the PR with `gh pr create`. Use the project's
   `.github/pull_request_template.md` as the body. Title format:
   `<type>(<scope>): <subject>` (Conventional Commits).
7. Report the PR URL and stop. Do not run `gh pr merge` — merging is
   a human decision.
8. After the human has merged the PR and any follow-through (pipeline
   re-runs, deploys) is done, proactively suggest `/clear` with a
   one-line handoff (open questions, premise of the next task), per
   the "Session hygiene" section in CLAUDE.md. Never suggest it
   mid-task or while anything is still running.

If any step blocks and the cause is non-obvious, stop and ask before
guessing.
