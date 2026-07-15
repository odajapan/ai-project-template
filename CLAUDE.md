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

## Session hygiene (/clear suggestions)

A long conversation carries the trial-and-error log of already-merged work into
the next task, where it is noise. Claude should **proactively suggest `/clear`
at natural milestones** — but only when ALL of these hold:

- The unit of work is complete: the PR is merged and any follow-through
  (pipeline re-runs, deploys) is done.
- Nothing is still running: no background agents, tasks, or benchmarks.
- The working tree is clean, and temporary worktrees / local branches are
  cleaned up.
- Knowledge worth keeping has been persisted: memory (progress, lessons),
  CLAUDE.md (spec changes), and the PR body (design decisions, measurements).

When suggesting, attach a one-line handoff for the next session (open
questions, the premise of the next task). Never suggest `/clear` mid-task,
with uncommitted changes, or while anything is still running — the context
needed to continue would be lost.
