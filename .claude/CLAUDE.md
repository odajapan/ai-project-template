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
src/your_project_name/   # Main package
  cli.py                 # Click CLI entry point
  utils.py               # Shared utility helpers
  llm.py                 # Claude API wrapper (with prompt caching)
  data/
    make_dataset.py      # Data pipeline entry point
tests/                   # pytest tests (mirror src/ structure)
data/
  raw/                   # Original immutable data
  interim/               # Intermediate transformed data
  processed/             # Final canonical datasets
  external/              # Third-party data
notebooks/               # Jupyter notebooks
models/                  # Serialized models
reports/figures/         # Generated figures
```

## Code Conventions

- Python 3.12+, type annotations on all public functions (`disallow_untyped_defs = true`)
- Line length: 88 (ruff default)
- No comments unless the WHY is non-obvious
- Tests use pytest; no mocking of internal logic unless testing I/O boundaries

## Environment Variables

Copy `.env.example` to `.env` before running code that calls the Claude API:

```bash
cp .env.example .env
# then fill in ANTHROPIC_API_KEY
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
