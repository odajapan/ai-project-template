# AGENTS.md

This file is the **shared source of truth for all AI coding agents** working in this
repository. Claude Code reads it via `@AGENTS.md` in `CLAUDE.md`. Other agents (Codex,
Cursor, GitHub Copilot, Gemini CLI, Jules, Aider, goose, …) read it directly.

Harness-specific configuration stays in each agent's native directory — Claude Code
specifics live under `.claude/`.

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
pip install -e ".[dev,claude]"   # or: make requirements
cp .env.example .env             # then fill in ANTHROPIC_API_KEY
```

Python 3.12+ required. Never commit `.env`.

---

## Commands

| Command | Description |
|---------|-------------|
| `make check` | **The gate** — lint (ruff) + type check (mypy) + tests (pytest) |
| `make lint` | Run ruff over `src/` and `tests/` |
| `make typecheck` | Run mypy over `src/` |
| `make test` | Run pytest |
| `make format` | Format with ruff |
| `make data` | Run the data pipeline |
| `make precommit` | Run pre-commit hooks against all files |

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
- Never overwrite `.env`; `.env.example` may be edited
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
  - Claude Code → `claude/<task>`, Codex → `codex/<task>`, etc.
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
  (summary, motivation, key changes, `make check` output, verification steps)
- **Never merge** — humans run `gh pr merge`

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
