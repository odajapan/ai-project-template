---
name: "source-command-finish-task"
description: "Verify checks, push the codex/* branch, and open a PR."
---

<!-- ported-from: .claude/commands/finish-task.md sha256:c1b634527035 -->

# source-command-finish-task

Use this skill when the user asks to run the migrated source command `finish-task`.

## Command Template

# /finish-task — wrap up an autonomous task

Run only after the `source-command-start-task` skill and the actual work are complete.

Steps:

1. `git status` — confirm there are no unintended files (data/raw/,
   .env, models/, generated artifacts). Abort and report if there are.
2. `git branch --show-current` — confirm we are on a `codex/*`
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
   `<type>(<scope>): <subject>` (Conventional Commits). Fill the
   `## Done when` section with the `Done when` lines from this task's
   scope declaration, verbatim — reviewers check the PR against them.
   If the task had no scope declaration, write the checks you
   actually ran instead; never leave the section as the template
   placeholder.
7. Report the PR URL. **Autonomous runs stop here.** In an interactive
   session, offer to watch CI; if the user agrees, run
   `gh pr checks <number> --watch` in the background and act on how it
   ends:
   - `no checks reported` (GitHub has not registered the run yet): wait
     30 s and start the watch again, up to 5 times, then report.
   - every check `pass` or `skipping` → say so and offer a review of the
     PR diff.
   - any check `fail` or `cancel` → report it with its URL and stop; the
     human decides whether to review a red PR.
   Do not run `gh pr merge` — merging is a human decision.
8. Once the human has merged the PR, any follow-through (pipeline
   re-runs, deploys) is done, nothing is still running, the tree is clean,
   and anything worth keeping is in the PR body or `AGENTS.md`, suggest
   starting a fresh session with a one-line handoff. Never mid-task.

If any step blocks and the cause is non-obvious, stop and ask before
guessing.
