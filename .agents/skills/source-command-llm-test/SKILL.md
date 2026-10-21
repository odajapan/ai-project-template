---
name: "source-command-llm-test"
description: "Verify the Claude (Anthropic) API is reachable and the project's ClaudeClient works end-to-end."
---

<!-- ported-from: .claude/commands/llm-test.md sha256:eca28fa670b5 -->

# source-command-llm-test

Use this skill when the user asks to run the migrated source command `llm-test`.

## Command Template

# /llm-test — verify Claude API setup

Run a smoke test that confirms the project can talk to the Claude (Anthropic) API
through `ClaudeClient`.

Steps:

1. Check that `ANTHROPIC_API_KEY` is set in the current shell, or have the
   snippet call `dotenv.load_dotenv()` first — never open `.env` yourself.
   If it is still missing, stop and tell me to copy `env.example` and fill it in.
2. Run a one-line Python snippet that imports `your_project_name.llm.ClaudeClient`,
   instantiates it, and calls `chat("Reply with the word PONG and nothing else.")`.
3. If the response contains `PONG`, report success along with `chat_with_tracking`'s
   token usage. Otherwise, report the exact error and which step failed.

Use the project's installed Python interpreter (`python -c "..."`) — do not
spawn a separate venv.
