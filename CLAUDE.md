@AGENTS.md

# Claude Code specifics

- Template baseline and harness map: `.claude/CLAUDE.md`
- Path-scoped rules (auto-loaded): `.claude/rules/`
- On-demand skills: `.claude/skills/`
- Slash commands: `.claude/commands/`

**Branch prefix for Claude Code sessions:** `claude/<task-name-kebab-case>`
(e.g. `claude/harden-for-autonomous-runs`).

**Autonomous runs** (`--dangerously-skip-permissions` or unattended sessions):
the guardrails in `AGENTS.md` are backed by `.claude/settings.json` deny rules —
force-push, push to `main`/`master`, `git reset --hard`, destructive `rm -rf`,
and reads *or writes* of real `.env` files and `secrets/`. **Merging is not
blocked by a deny rule** — the authoritative gate is GitHub branch protection
(`docs/branch-protection.md`). Autonomous runs must open the PR and stop. Use
`/start-task` to cut the branch and declare scope; use `/finish-task` to run
`make check`, push, and open the PR.

**Permission rules are tripwires, not a security boundary.** They match the
command text as a prefix: `Bash(rm -rf:*)` does not see `/bin/rm -rf` or
`bash -c '...'`, a `Read(.env)` deny does not stop a Python one-liner from
opening the file, and `curl`/`wget`/`python:*` reach the network freely.
The OS-level control is Claude Code's **sandbox** — filesystem `denyRead` /
`denyWrite` for `.env`, `secrets/`, `data/raw/`, `models/`, plus a network
`allowedDomains` allowlist. A ready-to-copy block is in
`.claude/settings.local.json.example`. It is off by default only because the
domain list has no one-size-fits-all value; set it per project before running
unattended somewhere exfiltration risk matters.

**The PostToolUse hook ruff-formats only the file just edited** (see
`.claude/hooks/format-edited-file.sh`); lint autofix stays in `make format`.

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
