---
name: codebase-onboarding
description: Map of this template — what's where, how to start a new project, and which files to read first.
---

# Codebase onboarding

## What this template provides

A Python 3.12+ project scaffold pre-wired for Claude AI development:
- `ClaudeClient` wrapper with caching, streaming, tool use, and multi-turn
- Click CLI (`ask` / `chat` subcommands) calling Claude out of the box
- `make check` = ruff + mypy + pytest in one command
- Claude Code config: opusplan model, role-based subagents, slash commands, skills

## Key files — read these first

| File | Why it matters |
|---|---|
| `src/your_project_name/llm.py` | All Claude API calls go through `ClaudeClient` here |
| `src/your_project_name/schemas.py` | Pydantic `ToolDefinition` — how tools are declared |
| `src/your_project_name/cli.py` | Click entry points; shows end-to-end usage |
| `CLAUDE.md` | Autonomous run rules — read before any unattended task |
| `.claude/CLAUDE.md` | Commands, skills, project structure overview |
| `pyproject.toml` | All dependencies; add new ones here only |
| `Makefile` | `make check`, `make requirements`, `make data` |

## Starting a new project from this template

1. Clone / copy the repo; rename `your_project_name` throughout:
   ```bash
   find . -type f | xargs grep -l "your_project_name" | head -20
   ```
2. Update `pyproject.toml`: `name`, `[project.scripts]` entry point.
3. `cp env.example .env` and fill in `ANTHROPIC_API_KEY`.
4. `make requirements` to install in editable mode.
5. `make check` — should be green before writing any code.
6. `/llm-test` inside Claude Code to verify API connectivity.

## Extending the template

| Task | Command |
|---|---|
| Add a Claude tool | `/add-tool <name>` |
| Add a runnable example | `/add-example <name>` |
| Add a path-scoped rule | `/new-rule <name>` |
| Start an autonomous task | `/start-task <task-name>` |

## What to keep, what to rename

Keep `.claude/` as-is — all config is project-agnostic.
Rename only `src/your_project_name/` and the matching `tests/` imports.
