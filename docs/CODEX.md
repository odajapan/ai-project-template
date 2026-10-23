# Codex parity — how the `.codex/` and `.agents/` copies are maintained

`.claude/` is the source of truth for agents and workflow commands. OpenAI
Codex reads neither `CLAUDE.md` nor `.claude/`, so it gets adapted copies:

| Source (Claude Code)          | Copy (Codex)                                   |
|-------------------------------|------------------------------------------------|
| `.claude/agents/<name>.md`    | `.codex/agents/<name>.toml`                    |
| `.claude/commands/<name>.md`  | `.agents/skills/source-command-<name>/SKILL.md` |
| `.claude/settings.json` hooks | `.codex/hooks.json`                            |

## Porting rules

- The copies are **adapted**, not generated: branch prefix `codex/`, Codex
  CLI flags and tool names, and no reliance on `CLAUDE.md`. When you change
  a source, port the change to its copy **by hand in the same PR**. Do not
  regenerate the copy, or the adaptations are lost.
- Each copy carries a `ported-from: <source> sha256:<12 hex>` marker. After
  porting, set it to the hash the failing test prints — the source's sha256
  with the package name normalized back to `your_project_name`.
- `tests/test_repo_consistency.py` fails when a copy is missing, malformed,
  stale against its source, or still uses the `claude/` prefix. The checks
  skip themselves once both `.codex/` and `.agents/` are deleted
  (`docs/TEMPLATE_INIT.md` Phase 1).
- Claude-only commands (`jira`, `daily-report`, `pr-review`) and
  `.claude/rules/` have no Codex copy. A rule that must also bind Codex goes
  in `AGENTS.md`.

## Known gaps on the Codex side

- Codex runs `.codex/hooks.json` only after the project's `.codex/` layer is
  trusted and the hook is approved via `/hooks`.
- The Codex PostToolUse hook still runs `make format` over the whole tree
  (Codex's `apply_patch` payload has no single edited-file path), so the
  ruff autofix race described in `.codex/agents/implementer.toml` still
  applies there. Claude Code's hook formats only the edited file.
- Codex subagents cannot be restricted to read-only per agent
  (`sandbox_mode` is not overridable in an agent file), so the "read-only"
  agents rely on their instructions.
- They set no `model`, so they run on the parent session's model — the
  haiku/sonnet/opus cost split in `.claude/agents/` has no Codex equivalent
  yet.
- Codex has no counterpart to the `.claude/settings.json` deny rules, so
  prefer the `workspace-write` sandbox over
  `--dangerously-bypass-approvals-and-sandbox`.
