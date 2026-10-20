---
name: "source-command-new-rule"
description: "Create a new path-scoped rule file under .claude/rules/."
---

# source-command-new-rule

Use this skill when the user asks to run the migrated source command `new-rule`.
`$ARGUMENTS` below stands for the argument the user gave with the request.

## Command Template

# /new-rule — create a path-scoped rule

Create a new file under `.claude/rules/$ARGUMENTS.md` that Claude Code loads
when working on matching files. Codex does not read `.claude/rules/`;
if the rule must also bind Codex, put it in `AGENTS.md` (or a nested
`AGENTS.md` in the matching directory) instead.

Steps:

1. Read an existing rule (e.g. `.claude/rules/testing.md`) to match the style
   and frontmatter format.
2. Ask me which file globs the rule should apply to (default: prompt me with
   3 likely candidates based on the rule name).
3. Write the new rule file using this template:

   ```markdown
   ---
   paths:
     - "src/**/<glob>"
   ---

   # <Title>

   ## <Section>
   - <Concrete, verifiable instruction>
   ```

4. Keep it under 50 lines. Concrete > comprehensive.

After writing, show me the file path so I can review it.
