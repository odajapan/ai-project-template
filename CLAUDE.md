# CLAUDE.md

This file is read by Claude Code to understand the project structure and conventions.

## Project Overview

A Python 3.12+ data science project template. The canonical package lives under
`src/your_project_name/`. After creating a new project from this template run:

```bash
./scripts/rename_project.sh my_new_project
```

## Key Commands

| Command | Description |
|---------|-------------|
| `make requirements` | Install project in editable mode with dev + common extras |
| `make check` | Lint (flake8) + type check (mypy) + tests (pytest) |
| `make lint` | Run flake8 over `src/` |
| `make typecheck` | Run mypy over `src/` |
| `make test` | Run pytest |
| `make format` | Format with black + isort |
| `make data` | Run the data pipeline (`src/.../data/make_dataset.py`) |
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
- Line length: 88 (black default)
- Imports: isort with `profile = "black"`
- No comments unless the WHY is non-obvious
- Tests use pytest; no mocking of internal logic unless testing I/O boundaries

## Environment Variables

Copy `.env.example` to `.env` before running code that calls the Claude API:

```bash
cp .env.example .env
# then fill in ANTHROPIC_API_KEY
```

## Dependencies

All dependency definitions live in `pyproject.toml`. The `requirements*.txt` files
are thin wrappers for convenient installation and should not be edited directly.

Optional extras:

| Extra | Contents |
|-------|----------|
| `dev` | pytest, flake8, black, isort, mypy, pre-commit |
| `claude` | anthropic SDK |
| `notebook` | jupyterlab, ipykernel |
| `viz` | matplotlib, seaborn |
| `cloud` | boto3, s3fs, aioboto3 |
| `dashboard` | streamlit, fastapi, uvicorn |
| `vision` | torch, torchvision, opencv-python, pillow |
| `bigquery` | google-cloud-bigquery, db-dtypes |
