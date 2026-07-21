# Template baseline — Claude Code instructions

This file is the template-provided baseline for Claude Code.
Project-specific instructions go in `./CLAUDE.md` at the repo root.

Portable baseline (commands, code conventions, testing, security, git workflow)
lives in `../AGENTS.md` — read that first.

@README.md

---

## Project Structure

```
src/your_project_name/
  cli.py           # Click CLI: hello / ask / chat (last two call Claude)
  utils.py         # Shared utility helpers
  llm.py           # Claude API wrapper (caching, streaming, tool use, multi-turn)
  schemas.py       # Pydantic models for tool definitions and structured output
  exceptions.py    # Project-level exception hierarchy
  data/
    make_dataset.py  # Data pipeline entry point
tests/             # pytest tests (mirror src/ structure)
examples/          # Runnable scripts: simple_chat / agent_loop / structured_extraction
.claude/
  CLAUDE.md        # This file — Claude Code baseline (harness-specific)
  agents/          # Role-based subagents
    code-reviewer.md   # Read-only PR/diff review (opus)
    data-analyst.md    # Read-only data/ diagnostics with pandas/DuckDB (sonnet)
    explorer.md        # Cheap read-only lookup (haiku)
    implementer.md     # Edit-capable feature/refactor/test work (sonnet)
    test-runner.md     # Run pytest/ruff and summarize pass/fail (haiku)
    verifier.md        # Adversarial check of a single claim/finding (opus)
  commands/        # Slash commands
    llm-test.md    # /llm-test   — verify Claude API connectivity
    add-tool.md    # /add-tool   — scaffold ToolDefinition + handler + test
    new-rule.md    # /new-rule   — create a path-scoped rule
    start-task.md  # /start-task — cut branch + declare scope
    finish-task.md # /finish-task — checks + push + PR
    land.md        # /land       — merge PR(s), retarget children, sync main, clean up
    debug.md       # /debug      — diagnose and fix a Python error
    add-example.md # /add-example — scaffold a runnable example script
    worktree.md    # /worktree   — show commands to spin up an isolated worktree
  rules/           # Path-scoped rules (auto-loaded by file context)
    data-pipeline.md      # src/**/data/**, notebooks/**
    data-raw-immutable.md # data/raw/** immutability guard
    llm-development.md    # src/**/llm.py, *client*.py, llm tests
    notebooks.md          # notebooks/**/*.ipynb conventions
    secrets.md            # .env, **/secrets/** guards
    testing.md            # tests/**, src/**
    web.md                # web/** TypeScript workspace conventions
  skills/          # Reference docs — mention by name to load
    agentic-engineering.md  # Claude agent patterns: tool use, loops, subagents
    api-design.md           # REST API design (tool-agnostic)
    claude-sdk.md           # ClaudeClient patterns: caching, streaming, tool use
    codebase-onboarding.md  # Map of this template, which files to read first
    error-handling.md       # Python error-handling conventions
    eval-harness.md         # Testing LLM outputs: deterministic, LLM-as-judge, golden set
    fastapi-patterns.md     # FastAPI router/Pydantic/ClaudeClient injection patterns
    python-testing.md       # pytest conventions, mocks, coverage
  settings.json    # Shared permissions, hooks, and model config
```

---

## Subagent delegation policy (token economy)

The main loop keeps design decisions and delegates mechanical work. Each
agent pins the cheapest model that does its job well:

| Task                                   | Agent           | Model  |
| -------------------------------------- | --------------- | ------ |
| "Where is X" lookups, read-only search | `explorer`      | haiku  |
| Run tests/lint, summarize pass/fail    | `test-runner`   | haiku  |
| Implement an agreed spec + tests       | `implementer`   | sonnet |
| Data diagnostics under `data/`         | `data-analyst`  | sonnet |
| Pre-PR review, design second opinion   | `code-reviewer` | opus   |
| Verify one claim/finding adversarially | `verifier`      | opus   |

Notes:

- The built-in `Explore` / `Plan` agents inherit the session model — for
  cheap lookups prefer the custom `explorer` (pinned to haiku).
- `code-reviewer` reviews a whole diff broadly; `verifier` judges a single
  claim (CONFIRMED / PLAUSIBLE / REFUTED). Feed verifier one finding at a
  time, ideally in parallel across findings.

---

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
- `/start-task <name>` — cut a `claude/<name>` branch and declare scope
- `/finish-task` — run checks, push, and open a PR
- `/land [<pr>...]` — merge PR(s), retarget stacked children, sync main, and clean up
- `/debug <traceback>` — diagnose and fix a Python error systematically
- `/add-example <name>` — scaffold a runnable script under `examples/`
- `/worktree` — show commands to spin up an isolated git worktree

ySkills (reference docs — mention by name to load):

- `claude-sdk` — ClaudeClient patterns: caching, streaming, tool use, multi-turn
- `python-testing` — pytest conventions and mock patterns
- `agentic-engineering` — agent loops, tool use, subagents, structured output
- `eval-harness` — testing LLM outputs: deterministic checks, LLM-as-judge, golden set
- `codebase-onboarding` — map of this template, which files to read first
- `error-handling` — Python error-handling conventions
- `api-design` — REST API design
- `fastapi-patterns` — FastAPI + Pydantic + ClaudeClient patterns
