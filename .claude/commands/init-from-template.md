---
description: First-run checklist — adapt the template to this project before the first feature task.
argument-hint: <new_project_name>
allowed-tools:
  - Bash
  - Read
  - Edit
  - Glob
  - Grep
common_files:
  - docs/TEMPLATE_INIT.md
  - pyproject.toml
  - Makefile
  - AGENTS.md
suggested_sequence:
  - confirm clean tree and cut claude/init-from-template
  - Phase 0 rename + install + green make check
  - ask the Phase 1 questions as a batch, wait for answers
  - delete only what the answers authorize
  - Phase 2 re-anchor docs and env.example
  - make check green, then stop
---

# /init-from-template — adapt the template to this project

Read `docs/TEMPLATE_INIT.md` and execute its three phases in order. The
argument `$ARGUMENTS` (if given) is the new project name for Phase 0;
otherwise ask for it.

This task cuts its own branch — it does not require `/start-task` first,
and it is **exempt from `/start-task`'s ">3 files / >500 lines" stop
condition**. Adapting a template legitimately touches many files and
deletes several. Declare the deletion set up front (from the Phase 1
answers) instead of treating file count as a stop signal.

Two constraints that matter more here than in a normal task:

1. **Ask all of Phase 1's questions in a single batch, then wait for the
   human's answers before deleting anything.** Never infer that a
   subsystem (LLM layer, data pipeline, Jira workflow, docs, web/) is
   unused from the absence of a call site in the codebase — this is a
   freshly cloned template, so nothing has been used yet regardless of
   what the final project will need.
2. **This task legitimately edits `env.example`.** Read it before editing,
   per `.claude/rules/secrets.md` — never append blind.

Steps:

1. `git status` — stop if the tree isn't clean.
2. `git checkout -b claude/init-from-template` (or ask for a different
   branch name if this isn't the first task on this clone).
3. Run Phase 0 from `docs/TEMPLATE_INIT.md` (rename script, `pyproject.toml`
   metadata, `make requirements`, `make check`, `make hooks`).
4. Ask the Phase 1 questions as one batch via the question tool available
   in this session. Wait for all answers before deleting anything.
5. Delete exactly what the answers authorize, plus any now-dangling
   references (Makefile targets, `AGENTS.md` Commands table, `pyproject.toml`
   extras, `.claude/CLAUDE.md`).
6. Run Phase 2 (rewrite `env.example`, trim `AGENTS.md`, refresh
   `.claude/CLAUDE.md`, rewrite `README.md`, sync `EXTRAS` across Makefile/CI).
7. Confirm the exit criteria in `docs/TEMPLATE_INIT.md`: `make check` green,
   `git grep -c your_project_name` is `0`, no dangling references to deleted
   files.
8. Commit as `chore: initialize project from template` and report what was
   kept vs. removed. Do not start a feature task in the same branch.
