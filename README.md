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
uv pip install -e ".[dev,claude,jira]"

# Heavier data-science extras (notebook/viz/docs/cloud), if this project
# needs them:
# uv pip install -e ".[dev,claude,jira,notebook,viz,docs,cloud]"
```

### 2. pip / venv

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -e ".[dev,claude,jira]"

# Heavier data-science extras (notebook/viz/docs/cloud), if this project
# needs them:
# pip install -e ".[dev,claude,jira,notebook,viz,docs,cloud]"
```

### 3. Conda

```bash
conda env create -f environment.yml
conda activate your_project_name
pip install -e ".[dev,claude,jira]"
```

### 4. Docker

```bash
docker build -t your_project_name:dev .
docker run --rm -it -v "$(pwd):/app" your_project_name:dev bash
```

### 5. Environment variables

```bash
cp env.example .env
# ANTHROPIC_API_KEY is only needed for the LLM layer (llm.py, ask/chat,
# examples/) — fill it in if this project uses it, otherwise leave it unset.
```

### 6. Pre-commit hooks (optional)

```bash
pre-commit install
```

### 7. Git branch guard hooks (recommended)

Wire the repo-local hooks in `.githooks/` so direct commits and pushes
to `main`/`master` are blocked locally:

```bash
make hooks
```

---

## Common commands

```bash
make requirements   # Install project in editable mode with the canonical extras (dev,claude,jira)
make requirements-all  # ...plus the heavier data-science extras (notebook,viz,docs,cloud)
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
├── env.example            ← Environment variable template
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
├── scripts/               ← Standalone CLI scripts (not part of the installable package)
│   ├── jira_task.py       ← Optional Jira <-> GitHub workflow: issue = branch = PR
│   ├── daily_report.py    ← Lists Jira tickets resolved on a given day
│   └── rename_project.sh
│
├── data/                  ← Shipped as an empty skeleton (.gitkeep only);
│   │                        contents are gitignored except .gitkeep
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
| `jira` | requests, pyyaml — optional Jira ↔ GitHub workflow (`scripts/jira_task.py`, see [docs/JIRA_GITHUB_WORKFLOW.md](docs/JIRA_GITHUB_WORKFLOW.md)) |

Install any combination:

```bash
uv pip install -e .[dev,claude,notebook,viz]
```

---

## Dependency management

1. **Adding dependencies** — edit `pyproject.toml`, then reinstall:
   ```bash
   uv pip install -e ".[dev,claude,jira]"
   ```

2. **Lockfiles** — generate with uv for fully reproducible environments:
   ```bash
   uv pip compile --extra dev --extra notebook pyproject.toml -o requirements.lock
   ```

3. **Do not edit `requirements.txt` directly** — it is a thin wrapper around
   `pyproject.toml`.

---

## Autonomous Claude Code runs

This template is set up so Claude Code can be invoked with
`--dangerously-skip-permissions` for long, hands-off tasks without the
session being able to do anything genuinely dangerous. The guardrails:

- `CLAUDE.md` "Autonomous run rules" — branching, commit, PR, and stop
  conditions.
- `.claude/settings.json` — `allow`/`deny` lists for the everyday
  autonomous-run commands; explicit denies for force push, push to
  `main`, `git reset --hard`, and reads *or writes* of `.env`. Merging
  is not enforced by a deny rule — see "Human merges" below and
  `docs/branch-protection.md` for the actual gate.
- `.claude/rules/data-raw-immutable.md`, `secrets.md`, `notebooks.md` —
  path-scoped guards that activate when matching files are in scope.
- `.githooks/pre-commit` and `.githooks/pre-push` — refuse direct
  commits and pushes to `main`/`master` and any `--force` push. Install
  with `make hooks`.
- `docs/branch-protection.md` — the GitHub-side server protections
  that make the above failsafe.

### Recommended flow

1. **Pre-flight**: scope declared, working tree clean, `make hooks`
   installed, no unstaged changes, `gh auth status` OK.
2. **Isolate** (optional but recommended) — run in a separate worktree:
   ```bash
   git worktree add ../$(basename "$PWD")-<task> -b claude/<task> origin/main
   cd ../$(basename "$PWD")-<task>
   ```
3. **Launch**:
   ```bash
   claude --dangerously-skip-permissions
   ```
4. **Inside the session**:
   - `/start-task <task-name>` — sync `main`, cut `claude/<task>`,
     re-read autonomous rules, declare scope, **stop**.
   - Confirm the scope with the human, then do the work.
   - `/finish-task` — run `make check`, commit in logical units, push
     `claude/<task>`, open the PR, report URL, **stop**.
5. **Human merges.** Claude never runs `gh pr merge`.

### Checklist before launching

- [ ] Scope declared with the human
- [ ] Isolated worktree or fresh `claude/*` branch
- [ ] Working tree clean (`git status`)
- [ ] `gh auth status` is green
- [ ] `make hooks` installed in the worktree
- [ ] GitHub branch protection on `main` is set
      (`docs/branch-protection.md`)

---

<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>.</small></p>
