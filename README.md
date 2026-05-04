# your_project_name

A template repository for Python-based data science projects, designed for
development with **Claude Code**.

This template assumes **Python 3.12 or later**.

After creating a new project from this template ("Use this template"), rename
the placeholder in one shot:

```bash
./scripts/rename_project.sh my_new_project
```

---

## Getting started

### 1. uv (recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager:

```bash
pip install uv          # or: brew install uv
uv pip install -e .[dev]

# Add optional extras as needed:
# uv pip install -e .[dev,notebook,viz,cloud,claude]
```

### 2. pip / venv

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e .[dev]

# Add optional extras as needed:
# pip install -e .[dev,notebook,viz,cloud,claude]
```

### 3. Conda

```bash
conda env create -f environment.yml
conda activate your_project_name
pip install -e .[dev]
```

### 4. Docker

```bash
docker build -t your_project_name:dev .
docker run --rm -it -v "$(pwd):/app" your_project_name:dev bash
```

### 5. Environment variables

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY and any other values
```

### 6. Pre-commit hooks (optional)

```bash
pre-commit install
```

---

## Common commands

```bash
make requirements   # Install project in editable mode with dev + common extras
make check          # Lint (ruff) + type check (mypy) + tests (pytest)
make lint           # Run ruff check over src/ and tests/
make format         # Format with ruff
make typecheck      # Run mypy on src/
make test           # Run pytest
make data           # Run the data pipeline
make precommit      # Run pre-commit hooks against all files
make activate       # Print the conda activate command
```

After installing the package, the CLI is available:

```bash
your_project_name hello
your_project_name hello Alice

# Talk to Claude (requires ANTHROPIC_API_KEY)
your_project_name ask "what is prompt caching?"
your_project_name chat        # interactive REPL
```

Runnable examples live in [`examples/`](examples/README.md):

```bash
python examples/simple_chat.py            # cached system prompt + token usage
python examples/agent_loop.py             # tool use loop
python examples/structured_extraction.py  # JSON → Pydantic
```

Slash commands available inside Claude Code:

- `/llm-test` — verify the Claude API works end-to-end
- `/add-tool <name>` — scaffold a new `ToolDefinition`
- `/new-rule <name>` — add a new path-scoped rule

---

## Project structure

```
├── CLAUDE.md              ← Project context for Claude Code
├── Makefile               ← Common workflow commands
├── README.md
├── pyproject.toml         ← Dependencies and tool configuration (single source of truth)
├── requirements.txt       ← Convenience wrapper (installs dev extras via pyproject.toml)
├── environment.yml        ← Conda environment definition
├── Dockerfile
├── .env.example           ← Environment variable template
├── .claude/
│   ├── CLAUDE.md          ← Template baseline instructions for Claude Code
│   ├── settings.json      ← Claude Code permissions and hooks
│   ├── commands/          ← Project-specific slash commands
│   └── rules/             ← Path-scoped rules loaded per file context
│
├── src/
│   └── your_project_name/
│       ├── cli.py         ← Click CLI: hello / ask / chat
│       ├── utils.py       ← Shared utility helpers
│       ├── llm.py         ← Claude API wrapper (caching, streaming, tools, multi-turn)
│       ├── schemas.py     ← Pydantic models for tool defs and structured output
│       └── data/
│           └── make_dataset.py  ← Data pipeline entry point
│
├── examples/              ← Runnable Claude API examples
│   ├── simple_chat.py
│   ├── agent_loop.py
│   └── structured_extraction.py
│
├── tests/
│   ├── test_cli.py
│   ├── test_utils.py
│   └── test_llm.py
│
├── data/
│   ├── raw/               ← Original immutable data
│   ├── interim/           ← Intermediate transformed data
│   ├── processed/         ← Final canonical datasets
│   └── external/          ← Third-party data
│
├── notebooks/             ← Jupyter notebooks
├── models/                ← Serialized models
├── reports/figures/       ← Generated figures
├── references/            ← Data dictionaries and manuals
└── docs/                  ← Sphinx documentation
```

---

## Optional extras

All dependency definitions live in `pyproject.toml`.

| Extra | Contents |
|-------|----------|
| `dev` | pytest, ruff, mypy, pre-commit |
| `claude` | anthropic SDK |
| `notebook` | jupyterlab, ipykernel |
| `viz` | matplotlib, seaborn |
| `docs` | Sphinx |
| `cloud` | boto3, s3fs, aioboto3, awscli |
| `dashboard` | streamlit, fastapi, uvicorn |
| `vision` | torch, torchvision, opencv-python, pillow |
| `bigquery` | google-cloud-bigquery, db-dtypes |

Install any combination:

```bash
uv pip install -e .[dev,claude,notebook,viz]
```

---

## Dependency management

1. **Adding dependencies** — edit `pyproject.toml`, then reinstall:
   ```bash
   uv pip install -e .[dev]
   ```

2. **Lockfiles** — generate with uv for fully reproducible environments:
   ```bash
   uv pip compile --extra dev --extra notebook pyproject.toml -o requirements.lock
   ```

3. **Do not edit `requirements.txt` directly** — it is a thin wrapper around
   `pyproject.toml`.

---

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>.</small></p>
