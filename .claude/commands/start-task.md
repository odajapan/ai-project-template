---
description: Cut a fresh claude/<task> branch from latest main and declare the task scope.
argument-hint: <task-name-kebab-case>
allowed-tools:
  - Bash
  - Read
common_files:
  - CLAUDE.md
  - .claude/CLAUDE.md
  - Makefile
  - pyproject.toml
suggested_sequence:
  - check git status
  - sync main
  - cut claude/<task> branch
  - re-read CLAUDE.md autonomous rules
  - emit scope declaration and wait for confirmation
---

# /start-task — begin an autonomous task

Bootstrap a new autonomous run. The user provided the task name as
`$ARGUMENTS` (kebab-case; if not, convert it).

Steps:

1. Run `git status` and stop with a clear message if there are
   uncommitted changes. Never `stash` or auto-commit on the user's
   behalf.
2. Run `git fetch origin --prune` and then
   `git checkout main && git pull --ff-only origin main` to sync.
3. Run `git checkout -b claude/$ARGUMENTS`. If the branch already
   exists, stop and ask the user whether to resume it or pick a new
   name.
4. Re-read the "Security & forbidden actions" and "Scope & stop conditions"
   sections of `AGENTS.md`, plus `.claude/CLAUDE.md`, so the constraints are
   fresh in context.
5. Emit a short scope declaration in this exact shape and stop for the
   user to confirm before any further work:

   ```
   ## Scope declaration — claude/$ARGUMENTS

   Goal: <one sentence>

   In scope:
     - <path or change>
     - <path or change>

   Out of scope:
     - <path or change>

   Done when:
     - <a check that comes back pass/fail: a test to turn green, a command
       and its expected output, a fixture to match — one line each>
     - <...>

   Stop conditions:
     - >3 files or >500 lines added beyond the in-scope set
     - any change to data/raw/, models/, or a real env file (.env, .env.local,
       …). Editing env.example is in scope.
     - tests fail in a way I cannot diagnose in 2 attempts
   ```

   `Done when` is the task's definition of done, written before the code
   exists so the review can be held against it instead of against "looks
   done". Derive it from the conversation; if the user has not said what
   done looks like, ask before emitting the declaration — except in an
   autonomous run (`--dangerously-skip-permissions` or unattended), which
   cannot wait for an answer: there, derive it from the task (`make
   check` exits 0 plus the test or command that proves the task's
   behavior) and mark each such line `(assumed)`, so the human sees in
   the PR which criteria they never agreed to. `/finish-task` copies
   these lines into the PR body and `/pr-review` checks each one.

Do not start editing files until the user confirms the scope.
