---
name: "source-command-add-tool"
description: "Scaffold a new ToolDefinition (Pydantic) plus a handler stub and unit test."
---

<!-- ported-from: .claude/commands/add-tool.md sha256:5d11ba5ced18 -->

# source-command-add-tool

Use this skill when the user asks to run the migrated source command `add-tool`.
`$ARGUMENTS` below stands for the argument the user gave with the request.

## Command Template

# /add-tool — scaffold a new Claude tool

Create a new tool that Claude can call via `ClaudeClient.chat_with_tools`.

The user provided the tool name as `$ARGUMENTS`. Convert it to:

- **snake_case** for the Python function and tool `name`
- A short human-readable description (ask the user once, then proceed)

Steps:

1. Read `src/your_project_name/schemas.py` and `src/your_project_name/llm.py`
   to confirm current conventions.
2. Add a new `ToolDefinition` instance to a new module
   `src/your_project_name/tools.py` (create it if absent), exporting
   the tool plus a handler function `def <name>(**kwargs) -> str`.
3. Add a unit test in `tests/test_tools.py` that verifies:
   - `tool.to_tool()` returns a dict with the expected `name`/`description`
   - The handler returns a string for valid input
4. Show me the diff and run `make check`.

Do not call the real Claude API. Tests must use mocks like the existing
`tests/test_llm.py`.
