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
   `^[a-z][a-z0-9_]*$`. If the human hasn't already named the project,
   derive a default suggestion from the repository directory name
   (lowercase, non-alphanumeric runs collapsed to `_`, leading
   non-letter characters stripped, trailing underscores stripped) and
   confirm it with the human — accept it, or a different name — before
   running the script. Never run the rename on a guessed name without
   confirmation: a repo
   directory name is rarely an intentional package-name decision.
2. Update `pyproject.toml`: `name`, `description`, `authors`, and
   `[project.scripts]` if the CLI entry point name should change.
3. `make requirements` (installs the canonical extras — see `AGENTS.md`
   Setup).
4. `make check` — must be green before continuing.
5. `make hooks` — installs the local branch-guard hooks.
6. Set up GitHub branch protection (`docs/branch-protection.md`) if this
   repo will use autonomous Claude Code runs.
7. Replace the owner in `.github/CODEOWNERS` with this project's
   maintainers — the template ships the template author's handle.
8. Lock dependencies: `uv lock` creates `uv.lock`; commit it and switch
   the CI install step to `uv sync --locked --extra dev --extra claude
   --extra jira` (or the project's canonical extras). Update the regex in
   `tests/test_repo_consistency.py::test_ci_extras_match_canonical` to
   read the `--extra` flags in the same edit, or `make check` goes red on
   the pattern it no longer finds. The template itself ships no lockfile
   so it never over-constrains downstream, but a real project should
   install the same versions in CI and locally.
9. If PRs should get an automatic Claude review, add the
   `ANTHROPIC_API_KEY` (or `CLAUDE_CODE_OAUTH_TOKEN`) repository secret
   — `.github/workflows/claude-code-review.yml` skips itself while the
   secret is absent. Reviews are billable API calls; set the secret only
   with the human's explicit go-ahead.

## Phase 1 — Prune

Ask the human all of these questions **in one batch**, then act only on the
answers. Do not infer that a subsystem is unused from the absence of a call
site — nothing in a freshly-cloned template has been used yet.

| Question | If **No**, delete |
|---|---|
| Does this project call the Claude API? | `src/**/llm.py`, `src/**/schemas.py`, `examples/`, `tests/test_llm.py`, `tests/integration/`, `.claude/rules/llm-development.md`, `.claude/commands/{llm-test,add-tool,add-example}.md`, `.claude/skills/{claude-sdk,agentic-engineering,eval-harness}/`, the `claude` extra in `pyproject.toml`, the `ask`/`chat` CLI commands in `cli.py`, the API-key block in `env.example` |
| Is there a data pipeline? | `src/**/data/`, `data/`, `notebooks/`, `models/`, `references/`, `reports/`, `.claude/rules/{data-pipeline,data-raw-immutable,notebooks}.md`, `.claude/agents/data-analyst.md`, the `make data` / `sync_data_*` Makefile targets, the `data/` negation block in `.gitignore`, the `nbstripout` pre-commit hook |
| Does this project use Jira? | `scripts/{jira_task.py,daily_report.py,daily_report.sh}`, `tests/scripts/`, `docs/JIRA_GITHUB_WORKFLOW.md`, `.claude/commands/{jira,daily-report}.md`, the `jira` extra in `pyproject.toml` and its allow rules in `.claude/settings.json`, `jira` in the Makefile `EXTRAS` default |
| Sphinx docs? | `docs/*.rst`, `docs/{conf.py,Makefile,make.bat}`, the `docs` extra |
| TypeScript workspace? | `.claude/rules/web.md`, the `web` CI job, the `AGENTS.md` §web section, `Bash(pnpm:*)` in `.claude/settings.json` |
| Will anyone use OpenAI Codex on this repo? | `.codex/`, `.agents/`, `docs/CODEX.md` and the Codex pointer at the top of `AGENTS.md` (the Codex checks in `tests/test_repo_consistency.py` skip themselves once both directories are gone) |
| Will PRs get an automatic Claude review in CI? (independent of whether the app itself calls Claude) | `.github/workflows/claude-code-review.yml`, Phase 0 step 9, the "Claude Code Review" note in `docs/branch-protection.md` |
| Does this project run as a long-lived service deployed to a host via a self-hosted GitHub Actions runner? | `deploy/`, `.github/workflows/deploy.yml`, `docs/EC2_DEPLOY.md`, `.claude/rules/ec2-deploy.md`, the `AGENTS.md` §EC2 deploy section |

Deleting a row's files also means removing any now-dangling references to
them elsewhere (Makefile targets, `AGENTS.md` Commands table,
`.claude/CLAUDE.md`, `pyproject.toml` extras). If Codex is kept, deleting a
`.claude/agents/<name>.md` or `.claude/commands/<name>.md` also means deleting
its copy, `.codex/agents/<name>.toml` or
`.agents/skills/source-command-<name>/`.

## Phase 2 — Re-anchor

1. Rewrite `env.example` for this project's real variables. **Read it
   first** — never append blind. Keep the format: `KEY=value` at column 0,
   no indentation, `#` comments (see `.claude/rules/secrets.md`). Enforced:
   `tests/test_repo_consistency.py::test_env_example_reviewed_after_template_rename`
   fails `make check` once `pyproject.toml` is renamed if `env.example`
   still matches the untouched template default byte-for-byte. If the
   template defaults are genuinely correct as-is, add a comment
   acknowledging the review instead of leaving the file untouched.
2. Trim `AGENTS.md` §Commands to targets that actually exist after Phase 1.
3. Refresh `.claude/CLAUDE.md` "Where things are" if entry points moved.
4. Rewrite `README.md` for this project.
5. If Phase 1 removed `jira` or added extras, update the Makefile `EXTRAS`
   default and `.github/workflows/ci.yml` to match — keep them identical
   (`tests/test_repo_consistency.py` checks this).
6. If Phase 1 kept the EC2 deploy scaffolding: `rename_project.sh` rewrites
   the `SERVICE`/`CONDA_ENV` variables inside `deploy/deploy_ec2.sh`, but
   `.service` isn't in its extension filter, so `deploy/your_project_name.service`
   gets neither renamed nor rewritten — its `Description`, `WorkingDirectory`,
   and `ExecStart` all still say `your_project_name` (the same category of
   file it warns about in its own "Not renamed" output, like `env.example`).
   Rename that file to match `SERVICE` in `deploy_ec2.sh` and fill in its
   real `Description`/`ExecStart`/`WorkingDirectory`/`ReadWritePaths`, then
   follow `docs/EC2_DEPLOY.md` to register the runner on the host — this is
   the step most likely to be skipped, and a `deploy.yml` with no registered
   runner behind it silently never deploys.
7. `rename_project.sh` skips `.claude/skills/codebase-onboarding/SKILL.md`
   entirely (its "Starting a new project from this template" section must
   keep saying `your_project_name` — that's instructions for a *future*
   user templating off this repo again, not a reference to this one).
   That means its "Key files" table, which legitimately should follow the
   rename, doesn't either. Update that table by hand to the new
   `src/<new_name>/` paths.
8. `make check` — must be green.
9. Commit as `chore: initialize project from template`.

## Exit criteria

Do not start the first feature task until all of these hold:

- `make check` passes.
- `git grep -c your_project_name` returns `0` (or only expected hits: this
  file, `.claude/commands/init-from-template.md` and its Codex copy
  `.agents/skills/source-command-init-from-template/SKILL.md`, and the bootstrap
  section of `.claude/skills/codebase-onboarding/SKILL.md` are intentionally
  excluded from the rename sed and always match; historical docs you
  intentionally kept; or `deploy/*.service` if you haven't renamed it yet
  — see Phase 2 step 6).
- No references remain to files deleted in Phase 1 (`make precommit`
  catches broken links via the standard hooks; also worth a manual
  `git grep` for filenames you removed).
