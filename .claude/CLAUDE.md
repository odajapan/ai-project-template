# Template baseline — Claude Code instructions

This file is the template-provided baseline for Claude Code.
Project-specific instructions go in `./CLAUDE.md` at the repo root.

Portable baseline (commands, code conventions, testing, security, git workflow)
lives in `../AGENTS.md` — read that first. Project-specific overview lives in
the repo root `README.md` — read it on demand, it is not auto-loaded.

---

## Where things are

| Concern | Entry point |
|---|---|
| Portable agent baseline | `../AGENTS.md` (read first) |
| Package source | `src/your_project_name/` — `cli.py` is the entry point |
| Tests | `tests/` (mirrors `src/`) |
| Gate | `make check` (see `Makefile`) |
| Standalone scripts | `scripts/` (not part of the installed package) |
| Long-lived service deploy (optional) | `docs/EC2_DEPLOY.md` |

Claude Code config under `.claude/`: `agents/`, `commands/`, `rules/`,
`skills/`, `settings.json`. **Do not maintain a file list here — it goes
stale.** To discover what exists, read each file's frontmatter
`description`: `head -5 .claude/{agents,commands,rules,skills}/*.md`.

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

After `make requirements` (or `pip install -e ".[dev,claude,jira]"`) and
setting `ANTHROPIC_API_KEY` in `.env`:

```bash
your_project_name ask "summarise prompt caching in one sentence"
your_project_name chat                 # interactive REPL
python examples/simple_chat.py         # runnable example
```

Slash commands (run inside Claude Code):

- `/init-from-template <name>` — first-run checklist: adapt the template
  to this project before the first feature task (see
  `docs/TEMPLATE_INIT.md`)
- `/llm-test` — verify Claude API connectivity
- `/add-tool <name>` — scaffold a new ToolDefinition + handler + test
- `/new-rule <name>` — create a path-scoped rule under `.claude/rules/`
- `/start-task <name>` — cut a `claude/<name>` branch and declare scope
- `/finish-task` — run checks, push, and open a PR
- `/land [<pr>...]` — merge PR(s), retarget stacked children, sync main, and clean up
- `/debug <traceback>` — diagnose and fix a Python error systematically
- `/add-example <name>` — scaffold a runnable script under `examples/`
- `/worktree` — show commands to spin up an isolated git worktree
- `/jira <subcommand>` — optional Jira ↔ GitHub workflow (issue = branch = PR);
  see `docs/JIRA_GITHUB_WORKFLOW.md`
- `/daily-report [--date YYYY-MM-DD]` — list Jira tickets completed on a day

Skills (reference docs — mention by name to load):

- `claude-sdk` — ClaudeClient patterns: caching, streaming, tool use, multi-turn
- `python-testing` — pytest conventions and mock patterns
- `agentic-engineering` — agent loops, tool use, subagents, structured output
- `eval-harness` — testing LLM outputs: deterministic checks, LLM-as-judge, golden set
- `codebase-onboarding` — map of this template, which files to read first
- `error-handling` — Python error-handling conventions
- `api-design` — REST API design
- `fastapi-patterns` — FastAPI + Pydantic + ClaudeClient patterns
