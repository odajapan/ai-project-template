# Template baseline — Claude Code instructions

This file is the template-provided baseline for Claude Code.
Project-specific instructions go in `./CLAUDE.md` at the repo root.

@README.md

## Key Commands

| Command | Description |
|---------|-------------|
| `make requirements` | Install project in editable mode with dev + common extras |
| `make check` | Lint (ruff) + type check (mypy) + tests (pytest) |
| `make lint` | Run ruff over `src/` and `tests/` |
| `make typecheck` | Run mypy over `src/` |
| `make test` | Run pytest |
| `make format` | Format with ruff |
| `make data` | Run the data pipeline |
| `make precommit` | Run pre-commit hooks against all files |
| `make activate` | Print the conda activate command for this project |

## Project Structure

```
src/your_project_name/
  cli.py           # Click CLI: hello / ask / chat (last two call Claude)
  utils.py         # Shared utility helpers
  llm.py           # Claude API wrapper (caching, streaming, tool use, multi-turn)
  schemas.py       # Pydantic models for tool definitions and structured output
  data/
    make_dataset.py  # Data pipeline entry point
tests/             # pytest tests (mirror src/ structure)
examples/          # Runnable scripts: simple_chat / agent_loop / structured_extraction
.claude/
  CLAUDE.md        # This file — template baseline
  commands/        # Project-specific slash commands (/llm-test, /add-tool, /new-rule)
  rules/           # Path-scoped rules loaded per file context
    llm-development.md
    testing.md
    data-pipeline.md
  settings.json    # Shared permissions and hooks
```

## Quick Start with Claude

After `pip install -e .[claude]` and setting `ANTHROPIC_API_KEY`:

```bash
your_project_name ask "summarise prompt caching in one sentence"
your_project_name chat                 # interactive REPL
python examples/simple_chat.py         # runnable example
```

Slash commands (run inside Claude Code):

- `/llm-test` — verify Claude API connectivity
- `/add-tool <name>` — scaffold a new ToolDefinition + handler + test
- `/new-rule <name>` — create a path-scoped rule under `.claude/rules/`

## Code Conventions

- Python 3.12+; type annotations required on all public functions
- Line length: 88 (ruff)
- No comments unless the WHY is non-obvious
- Tests in `tests/`; mock only at system boundaries (external APIs, file I/O)

## Security

- Never commit `.env` — use `.env.example` as the template
- `.env` and secrets stay in environment variables only
- `settings.json` deny rules block Claude from reading `.env` directly
- Sanitize any third-party data before storing results in `references/`

## Testing Standards

- All public functions require at least one test
- Mock `anthropic.Anthropic` for LLM unit tests — no real API calls in CI
- Integration tests (real API) go in `tests/integration/` and are skipped by `make test`
- Run `pytest tests/ --cov=src --cov-report=term-missing` to check coverage

## Git Workflow

- Branch naming: `feat/`, `fix/`, `docs/`, `chore/`
- Run `make check` before pushing
- PR titles follow Conventional Commits: `feat(module): description`

## Environment Variables

Copy `.env.example` to `.env` before running code that calls the Claude API:

```bash
cp .env.example .env
# fill in ANTHROPIC_API_KEY
```

## Dependencies

All dependency definitions live in `pyproject.toml`. Do not edit `requirements*.txt` directly.

| Extra | Contents |
|-------|----------|
| `dev` | pytest, ruff, mypy, pre-commit |
| `claude` | anthropic SDK |
| `notebook` | jupyterlab, ipykernel |
| `viz` | matplotlib, seaborn |
| `cloud` | boto3, s3fs, aioboto3 |
| `dashboard` | streamlit, fastapi, uvicorn |
| `vision` | torch, torchvision, opencv-python, pillow |
| `bigquery` | google-cloud-bigquery, db-dtypes |
