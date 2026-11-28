# AGENTS.md

This file is the **shared source of truth for all AI coding agents** working in this
repository. Claude Code reads it via `@AGENTS.md` in `CLAUDE.md`. Other agents
(Cursor, GitHub Copilot, Gemini CLI, Jules, Aider, goose, …) read it directly.

Harness-specific configuration stays in each agent's native directory — Claude Code
under `.claude/`. Nothing else in this repo mirrors those files.

---

## Project overview

Python 3.12+ AI/data-science project template. Click CLI, Pydantic v2, optional
Anthropic SDK (`claude` extra). Provides scaffolding for LLM-backed CLIs, data
pipelines, and AI agent loops.

**App LLM layer:** `src/your_project_name/llm.py` is Anthropic-only (`ClaudeClient`).
There is no multi-provider abstraction — do not assume OpenAI, Gemini, or other
providers are wired in. Adding another provider is a deliberate, scoped change.

---

## Setup

```bash
pip install -e ".[dev,claude,jira]"   # or: make requirements
cp env.example .env                   # only if this project uses the LLM layer
```

Python 3.12+ required. Never commit `.env`.

A clone or worktree needs its own environment: a shared env's editable
install points at one checkout's `src/`. `make venv` creates `.venv` in the
checkout and every `make` target uses it without activation (`make which_src`
shows what make resolves); running `python scripts/x.py` or the CLI directly
needs `.venv/bin/python` or `PYTHONPATH=$PWD/src`.

`ANTHROPIC_API_KEY` is required only for `src/your_project_name/llm.py`, the
`ask`/`chat` CLI commands, and `examples/`. `make check` passes without it —
unit tests mock `anthropic.Anthropic`. Projects with no LLM layer can delete
the key and the LLM scaffolding entirely.

---

## Commands

| Command | Description |
|---------|-------------|
| `make check` | **The gate** — lint (ruff) + type check (mypy) + tests (pytest) |
| `make venv` | Create this checkout's own `.venv` with the canonical extras; `make` targets use it without activation |
| `make which_src` | Print the interpreter, `PYTHONPATH`, and package path `make` resolves |
| `make lint` | Run ruff over `src/` and `tests/` |
| `make typecheck` | Run mypy over `src/` |
| `make test` | Run pytest |
| `make format` | Format with ruff |
| `make data` | Run the data pipeline |
| `make precommit` | Run the pre-commit hooks over all files, on demand — `make hooks` points `core.hooksPath` at `.githooks/` (branch guards only), so nothing lints at commit time; `make check` is the gate |

Run a single test:
```bash
pytest tests/path/to/test_file.py::test_name -v
```

---

## Code style & conventions

- Python 3.12+; type annotations required on **all public functions**
- Line length: 88 (ruff default)
- No comments unless the WHY is non-obvious (what the code does is readable; why it
  does it may not be)
- Pydantic v2 models for structured data; `ToolDefinition` in `schemas.py` for Claude
  tool definitions
- Write code that matches the surrounding style — same comment density, naming, idiom

Key locations:
- LLM wrapper: `src/your_project_name/llm.py`
- Tool definitions & structured output models: `src/your_project_name/schemas.py`
- CLI entry points: `src/your_project_name/cli.py`
- Runnable examples: `examples/`

---

## Testing

- Tests live in `tests/`, mirroring `src/` structure
- Mock **only at system boundaries** (external APIs, file I/O) — not internal helpers
- **No real/billable API calls in CI**: mock `anthropic.Anthropic` for unit tests
- Integration tests (real API) go in `tests/integration/` and are skipped by `make test`
- All public functions require at least one test
- Coverage: `pytest tests/ --cov=src --cov-report=term-missing`

---

## web/ (optional TypeScript workspace)

Some downstream projects add a TypeScript workspace under `web/`
(dashboards, UIs). It may not exist in every project.

| Command (run from `web/`) | Description |
|---------------------------|-------------|
| `pnpm install` | Install dependencies |
| `pnpm lint` | ESLint |
| `pnpm typecheck` | `tsc --noEmit` |
| `pnpm test` | Unit tests |
| `pnpm build` | Production build |

- TypeScript `strict: true`; pnpm is the package-manager convention
  (follow the existing lockfile if the project uses npm/yarn)
- Unit tests are colocated with sources and make no real network calls
- **`make check` does not cover `web/`** — run the pnpm commands above
  before every commit that touches `web/`
- CI runs the `web` job only when `web/package.json` exists
- Never commit `node_modules/`, build output, or `.env.local`; never
  embed API keys in client-side code

---

## Security & forbidden actions

These apply to every agent, unconditionally:

- Never write secrets (`ANTHROPIC_API_KEY`, cloud tokens, DB passwords) into source,
  commits, or logs — use placeholders in examples
- `data/raw/` is **immutable** — no edits, moves, or deletions
- Never read or write `.env` / `.env.*` / `secrets/**`. `env.example` is an
  ordinary committed file — read it before editing and match its formatting
  (`KEY=value`, no indentation)
- Never delete existing files under `models/`
- No `git push --force`, `git reset --hard origin/*`, or `git rebase -i` against
  published history
- Billable external API calls (Anthropic API, cloud APIs) only with **explicit
  confirmation** from the human — tests must use mocks/stubs
- Sanitize any third-party data before storing results in `references/`

---

## Branch, commit & PR workflow

- **Never commit or push directly to `main` / `master`**
- One task → one branch → one PR; don't pile unrelated changes together
- Branch name: **`<agent>/<task-name-kebab-case>`**
  - Claude Code → `claude/<task>`, Cursor → `cursor/<task>`, etc.
  - Start from latest `main`:
    ```bash
    git fetch origin --prune
    git checkout main && git pull --ff-only origin main
    git checkout -b <agent>/<task-name>
    ```
- **Conventional Commits**: `feat:`, `fix:`, `chore:`, `docs:`, `test:`, `refactor:`
  — optional scope in parentheses (`feat(llm): …`). Split by logical unit.
- Run `make check` before **every** commit; fix failures before committing — never
  commit a red tree
- Open PR with `gh pr create`; body must follow `.github/pull_request_template.md`
  (sections: Summary, Motivation, Key changes, Test results, Done when,
  Verification steps, Related issues, Checklist — paste the `make check`
  output under Test results; `tests/test_repo_consistency.py` keeps this
  list and the template's headings in step)
- **Merging is human-initiated, not autonomous.** In an interactive
  session, when the human says a PR is ready (e.g. via `/land`), Claude
  may run `gh pr merge`. The authoritative gate is **GitHub branch
  protection** (required CI + review — see `docs/branch-protection.md`),
  not the local permission rules. **Autonomous runs
  (`--dangerously-skip-permissions`) must never merge** — open the PR and
  stop.
- **Base every PR on `main`.** Do not stack a PR on a sibling feature
  branch — when that base branch is deleted on merge, GitHub auto-closes
  the child PR instead of retargeting it.

### Optional: Jira ↔ GitHub workflow

Projects that track work in Jira can use `scripts/jira_task.py` instead of
hand-rolling branches: **one Jira issue = one branch = one PR**. It creates
the issue, branches, transitions status (by name — no hard-coded workflow
IDs, so it works against any Jira project's own status names), and links
the PR back to the issue. Setup and full command reference:
[docs/JIRA_GITHUB_WORKFLOW.md](docs/JIRA_GITHUB_WORKFLOW.md). This is
purely additive — skip it entirely if the project doesn't use Jira.

### Keeping up with the template

A project created from this template has no git link back to it. The
baseline in `.claude/template-sync.ini` records the template commit this
project has reviewed up to; `/template-sync` (Claude Code) or the manual
procedure in [docs/TEMPLATE_SYNC.md](docs/TEMPLATE_SYNC.md) lists the
template PRs since then, classifies each (harness / gate / deps /
scaffold / docs / pruned), and ports the ones the human picks — one
commit per template PR, the rest recorded in the ini with a reason. A
session-start hook and the `/start-task` / `/land` milestones print a
one-line notice when the template has moved; nothing syncs on its own,
and an autonomous run only produces the review table. Delete the ini
file to opt out.

### Optional: EC2 self-hosted-runner deploy

Projects that run as a long-lived service (a dashboard, an API) can
auto-deploy on every merge to `main`: `deploy/deploy_ec2.sh` +
`.github/workflows/deploy.yml`, triggered by a self-hosted GitHub Actions
runner registered on the deploy host (`deploy/install_github_runner.sh`).
CI must pass before deploy runs, and the deploy pins to the exact commit
CI tested. Setup and the full runbook:
[docs/EC2_DEPLOY.md](docs/EC2_DEPLOY.md). This is purely additive — skip
it entirely if the project has no long-lived service to deploy.

**The runner registration step is manual and easy to forget** — adding
the workflow file alone does nothing; without a registered runner online,
every merge just queues a `Deploy` run that never starts. Verify with
`gh api /repos/<org>/<repo>/actions/runners` after setup. Two more
one-time settings are just as easy to skip: the `RUNNER_CHECK_TOKEN`
secret (a fine-grained PAT with Administration: read — `GITHUB_TOKEN`
cannot list runners) and the `DEPLOY_ENABLED=true` repository variable,
without which merge-triggered deploys are skipped.

---

## Scope & stop conditions

- At the start of a task, declare what is **in scope** and what is **out of scope**
- If the change unexpectedly grows beyond declared scope (more than 3 files or
  500 lines beyond what was promised), **stop and report** before continuing
- If tests fail in a way that isn't resolved within **two diagnostic attempts**,
  stop and report

---

## Uncertainty handling

- When a design decision is ambiguous, do **not** pick one and proceed — list the
  options with trade-offs and ask the human
- When unsure whether a library API is current, fetch the docs or ask rather than
  guessing — never assume from training data
