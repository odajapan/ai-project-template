# Template initialization checklist

Run this **once**, right after cloning the template and before the first
feature task. "Adapt the template to this project" is a distinct piece of
work from "do the first feature" — mixing them is how a downstream project
ended up editing `.env.example` blindly on day one and corrupting it (see
the git history around the `env.example` rename for the full story). This
checklist exists to separate the two.

Driven by `/init-from-template <name>`, or by hand following the phases
below.

## Phase 0 — Identity

1. `./scripts/rename_project.sh <new_name>` (use `--dry-run` first if
   unsure). `<new_name>` must be a valid Python identifier:
   `^[a-z][a-z0-9_]*$`.
2. Update `pyproject.toml`: `name`, `description`, `authors`, and
   `[project.scripts]` if the CLI entry point name should change.
3. `make requirements` (installs the canonical extras — see `AGENTS.md`
   Setup).
4. `make check` — must be green before continuing.
5. `make hooks` — installs the local branch-guard hooks.
6. Set up GitHub branch protection (`docs/branch-protection.md`) if this
   repo will use autonomous Claude Code runs.

## Phase 1 — Prune

Ask the human all of these questions **in one batch**, then act only on the
answers. Do not infer that a subsystem is unused from the absence of a call
site — nothing in a freshly-cloned template has been used yet.

| Question | If **No**, delete |
|---|---|
| Does this project call the Claude API? | `src/**/llm.py`, `src/**/schemas.py`, `examples/`, `tests/test_llm.py`, `tests/integration/`, `.claude/rules/llm-development.md`, `.claude/commands/{llm-test,add-tool,add-example}.md`, `.claude/skills/{claude-sdk,agentic-engineering,eval-harness}.md`, the `claude` extra in `pyproject.toml`, the `ask`/`chat` CLI commands in `cli.py`, the API-key block in `env.example` |
| Is there a data pipeline? | `src/**/data/`, `data/`, `notebooks/`, `models/`, `references/`, `reports/`, `.claude/rules/{data-pipeline,data-raw-immutable,notebooks}.md`, `.claude/agents/data-analyst.md`, the `make data` / `sync_data_*` Makefile targets, the `data/` negation block in `.gitignore`, the `nbstripout` pre-commit hook |
| Does this project use Jira? | `scripts/{jira_task.py,daily_report.py,daily_report.sh}`, `tests/scripts/`, `docs/JIRA_GITHUB_WORKFLOW.md`, `.claude/commands/{jira,daily-report}.md`, the `jira` extra in `pyproject.toml` and its allow rules in `.claude/settings.json`, `jira` in the Makefile `EXTRAS` default |
| Sphinx docs? | `docs/*.rst`, `docs/{conf.py,Makefile,make.bat}`, the `docs` extra |
| TypeScript workspace? | `.claude/rules/web.md`, the `web` CI job, the `AGENTS.md` §web section, `Bash(pnpm:*)` in `.claude/settings.json` |

Deleting a row's files also means removing any now-dangling references to
them elsewhere (Makefile targets, `AGENTS.md` Commands table,
`.claude/CLAUDE.md`, `pyproject.toml` extras).

## Phase 2 — Re-anchor

1. Rewrite `env.example` for this project's real variables. **Read it
   first** — never append blind. Keep the format: `KEY=value` at column 0,
   no indentation, `#` comments (see `.claude/rules/secrets.md`).
2. Trim `AGENTS.md` §Commands to targets that actually exist after Phase 1.
3. Refresh `.claude/CLAUDE.md` "Where things are" if entry points moved.
4. Rewrite `README.md` for this project.
5. If Phase 1 removed `jira` or added extras, update the Makefile `EXTRAS`
   default and `.github/workflows/ci.yml` to match — keep them identical
   (`tests/test_repo_consistency.py` checks this).
6. `make check` — must be green.
7. Commit as `chore: initialize project from template`.

## Exit criteria

Do not start the first feature task until all of these hold:

- `make check` passes.
- `git grep -c your_project_name` returns `0` (or only expected hits, e.g.
  in historical docs you intentionally kept).
- No references remain to files deleted in Phase 1 (`make precommit`
  catches broken links via the standard hooks; also worth a manual
  `git grep` for filenames you removed).
