---
description: Verify checks, push the claude/* branch, open a PR, and start /pr-review while CI runs.
argument-hint: "[--no-fix]"
allowed-tools:
  - Bash
  - Read
  - Skill
common_files:
  - .github/pull_request_template.md
  - CLAUDE.md
suggested_sequence:
  - verify no forbidden files in git status
  - confirm on claude/* branch
  - run make check
  - commit uncommitted changes with conventional commits
  - git push origin <branch>
  - gh pr create with PR template (Done when filled in)
  - report PR URL; autonomous runs stop
  - interactive: watch CI in the background and run /pr-review at once
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
   `<type>(<scope>): <subject>` (Conventional Commits). Fill the
   `## Done when` section with the `Done when` lines from this task's
   scope declaration, verbatim — `/pr-review` reads them from the PR
   body. If the task had no scope declaration, write the checks you
   actually ran instead; never leave the section as the template
   placeholder.
7. Report the PR URL. **Autonomous runs stop here.** In an interactive
   session, do not wait for CI: start `gh pr checks <number> --watch` in
   the background and invoke `/pr-review` at once, forwarding `--no-fix`
   when `$ARGUMENTS` contains it. The review's gate is the `make check`
   step 3 already ran, so CI and the review run in parallel instead of
   in series. Say in one line that the default fix loop commits and
   pushes fixes to the branch (`/finish-task --no-fix` is the read-only
   alternative). When the watch ends, act on how:
   - `no checks reported` (GitHub has not registered the run yet): wait
     30 s and start the watch again, up to 5 times, then report.
   - every check `pass` or `skipping` → say so in one line, in the
     `/pr-review` report if it has not been written yet.
   - any check `fail` or `cancel` → report it with its URL and the head
     SHA it ran on (the fix loop may have pushed a newer head by then).
     A CI failure is not a review finding whichever head it hit: finish
     the review, then leave the fix to the human.
   `/land` waits for CI itself, so nobody needs to poll it afterwards.
   Do not run `gh pr merge` — merging is a human decision.
8. After the human has merged the PR and any follow-through (pipeline
   re-runs, deploys) is done, proactively suggest `/clear` with a
   one-line handoff (open questions, premise of the next task), per
   the "Session hygiene" section in CLAUDE.md. Never suggest it
   mid-task or while anything is still running.

If any step blocks and the cause is non-obvious, stop and ask before
guessing.
