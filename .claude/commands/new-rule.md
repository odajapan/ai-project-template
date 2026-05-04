---
description: Create a new path-scoped rule file under .claude/rules/.
argument-hint: <rule_name>
allowed-tools:
  - Read
  - Write
---

# /new-rule — create a path-scoped rule

Create a new file under `.claude/rules/$ARGUMENTS.md` that Claude Code loads
when working on matching files.

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
