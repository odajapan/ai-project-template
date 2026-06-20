@AGENTS.md

# Claude Code specifics

- Template baseline and harness map: `.claude/CLAUDE.md`
- Path-scoped rules (auto-loaded): `.claude/rules/`
- On-demand skills: `.claude/skills/`
- Slash commands: `.claude/commands/`

**Branch prefix for Claude Code sessions:** `claude/<task-name-kebab-case>`
(e.g. `claude/harden-for-autonomous-runs`).

**Autonomous runs** (`--dangerously-skip-permissions` or unattended sessions):
the guardrails in `AGENTS.md` are enforced by `.claude/settings.json` deny rules —
they block `gh pr merge`, force-push, push to `main`, direct `.env` reads, and
destructive `rm -rf` of `data/raw/`, `models/`, `.git`. Use `/start-task` to cut
the branch and declare scope; use `/finish-task` to run `make check`, push, and
open the PR.
