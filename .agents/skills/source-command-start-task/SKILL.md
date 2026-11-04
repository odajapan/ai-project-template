---
name: "source-command-start-task"
description: "Cut a fresh codex/<task> branch from latest main and declare the task scope."
---

<!-- ported-from: .claude/commands/start-task.md sha256:ec153c5475cc -->

# source-command-start-task

Use this skill when the user asks to run the migrated source command `start-task`.
`$ARGUMENTS` below stands for the argument the user gave with the request.

## Command Template

# /start-task — begin an autonomous task

Bootstrap a new autonomous run. The user provided the task name as
`$ARGUMENTS` (kebab-case; if not, convert it).

Steps:

1. Run `git status` and stop with a clear message if there are
   uncommitted changes. Never `stash` or auto-commit on the user's
   behalf.
2. Run `git fetch origin --prune` and then
   `git checkout main && git pull --ff-only origin main` to sync.
3. Run `git checkout -b codex/$ARGUMENTS`. If the branch already
   exists, stop and ask the user whether to resume it or pick a new
   name.
4. Re-read the "Security & forbidden actions" and "Scope & stop conditions"
   sections of `AGENTS.md` so the constraints are fresh in context.
5. Emit a short scope declaration in this exact shape and stop for the
   user to confirm before any further work:

   ```
   ## Scope declaration — codex/$ARGUMENTS

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
   done looks like, ask before emitting the declaration. The
   `source-command-finish-task` skill copies these lines into the PR body
   so reviewers can check each one.

Do not start editing files until the user confirms the scope.
