---
paths:
  - ".env"
  - ".env.*"
  - "**/*.env"
  - "**/secrets/**"
---

# Secrets handling

## Why this matters

`.env` and anything under `secrets/` hold credentials (Anthropic API keys,
cloud tokens, DB passwords). They must never appear in commits, code,
logs, PR descriptions, or chat output.

## Rules

- **Do not read** `.env` files or anything under `secrets/`. The deny
  rules in `.claude/settings.json` enforce this for the Read tool; do
  not try to work around it with `cat`, `head`, or shell redirection.
- **Edit only** `.env.example`, never `.env`. The example is the
  template; the real file is per-environment and stays out of source
  control.
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
