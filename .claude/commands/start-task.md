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
4. Re-read `CLAUDE.md` "Autonomous run rules" and `.claude/CLAUDE.md`
   so the constraints are fresh in context.
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

   Stop conditions:
     - >3 files or >500 lines added beyond the in-scope set
     - any change to data/raw/, models/, or .env*
     - tests fail in a way I cannot diagnose in 2 attempts
   ```

Do not start editing files until the user confirms the scope.
