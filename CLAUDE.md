# Project-specific instructions

Add project-specific commands, conventions, or context here.
The template baseline (key commands, structure, code conventions) is in `.claude/CLAUDE.md`.

<!-- Examples of what to add here:
## Domain context
This service processes financial transactions for ...

## Additional commands
- `make migrate` — run DB migrations

## Conventions specific to this project
- All monetary values stored as integers (yen, no decimals)
-->

## Autonomous run rules

These rules apply whenever Claude Code is invoked with
`--dangerously-skip-permissions`, or in any session expected to run for
more than a few minutes without an interactive reviewer. They override
ad-hoc preferences for the duration of the session.

### Branching

- **Never commit or push directly to `main` / `master`.**
- Start every task from the latest `main`:
  ```bash
  git fetch origin --prune
  git checkout main && git pull --ff-only origin main
  git checkout -b claude/<task-name-kebab-case>
  ```
- One task → one branch → one PR. Don't pile unrelated changes onto a
  single branch.
- Branch name format: `claude/<task-name-kebab-case>` (for example,
  `claude/harden-for-autonomous-runs`).

### Commits

- Use **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:`,
  `test:`, `refactor:`. Optional scope in parentheses
  (`feat(llm): ...`).
- Split by logical unit. A "fix a bug + refactor + add docs" change is
  three commits, not one.
- Run `make check` before every commit. If it fails, fix the cause and
  re-run — never commit a red tree.

### PR workflow

- Open the PR with `gh pr create` when the work is complete.
- The PR body must follow `.github/pull_request_template.md`. Cover
  summary, motivation, key changes, test results (output of
  `make check`), verification steps, related issues.
- **Never merge.** Humans handle `gh pr merge`. Claude must not invoke
  it (the deny rule in `.claude/settings.json` enforces this).

### Forbidden destructive actions

- No edits, moves, or deletions under `data/raw/` (immutable).
- No creation or overwrite of `.env`. `.env.example` may be edited.
- Never write secrets (`ANTHROPIC_API_KEY`, cloud tokens, DB
  passwords) into source, commits, or logs. Use placeholders in
  examples.
- External billable API calls (real Anthropic API, cloud APIs) only
  with explicit confirmation. Tests must use mocks or stubs.
- No deletion of existing files under `models/`.
- No remote-reflecting `git push --force`, `git reset --hard origin/*`,
  or `git rebase -i` against published history.

### Scope and stop conditions

- At the start of a task, declare in chat what's **in scope** and what's
  **out of scope** (use the template in `/start-task`).
- If the change unexpectedly grows beyond the declared scope (more than
  three files or more than 500 lines beyond what was promised), stop
  and report before continuing.
- If tests fail in a way that isn't resolved within two diagnostic
  attempts, stop and report.

### Uncertainty handling

- When a design decision is ambiguous, do **not** pick one and proceed
  — list the options with trade-offs and ask the human.
- When unsure whether a library API is current, fetch the docs (or
  ask) rather than guessing.
