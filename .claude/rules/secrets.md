---
paths:
  - ".env"
  - ".env.*"
  - "**/*.env"
  - "env.example"
  - "**/secrets/**"
---

# Secrets handling

## Why this matters

`.env` and anything under `secrets/` hold credentials (Anthropic API keys,
cloud tokens, DB passwords). They must never appear in commits, code,
logs, PR descriptions, or chat output.

## Two kinds of file — do not confuse them

**Real env files — never read, never write.**
`.env`, `.env.local`, `.env.production`, `**/*.env`, anything under
`secrets/`. The deny rules in `.claude/settings.json` block Read *and*
Edit on these. Do not work around them with `cat`, `head`, `git show`,
or shell redirection.

**`env.example` — an ordinary source file.**
It contains placeholders only, is committed to git, and is readable and
editable like any other file. When adding a variable:
- **Read the file first.** Never append blind.
- Match the existing format exactly: `KEY=value` at column 0, **no
  leading whitespace** (indented lines break `docker --env-file` and
  systemd `EnvironmentFile=`), `#` for comments, blank line between
  sections.
- Placeholders only — `<your-api-key>`, never a real value.

## Rules

- When demonstrating values in code, examples, or PR bodies, always use
  placeholders such as `<your-api-key>` or `${ANTHROPIC_API_KEY}`. Never
  hard-code a real key, even temporarily.
- Do not echo `os.environ["ANTHROPIC_API_KEY"]` (or similar) to stdout,
  logs, or test output. If a debugging step needs the value, mask it
  (`****` plus the last 4 characters).

## When in doubt

Treat any value labeled `KEY`, `TOKEN`, `SECRET`, `PASSWORD`, or
`CREDENTIALS` as sensitive and stop to ask the human before storing,
copying, or transmitting it.
