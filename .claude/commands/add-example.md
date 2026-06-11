---
description: Scaffold a new runnable example script under examples/. Shows how to use a specific project feature end-to-end.
argument-hint: <example_name>
allowed-tools:
  - Read
  - Write
  - Bash
common_files:
  - examples/
  - src/your_project_name/llm.py
  - src/your_project_name/schemas.py
suggested_sequence:
  - read existing examples for style reference
  - identify which feature to demonstrate
  - write examples/<name>.py
  - run the script with python examples/<name>.py to verify it executes
  - update README if the example adds a new usage pattern
---

# /add-example — add a runnable example script

Create a self-contained script in `examples/` that demonstrates a specific
feature of the project.

The user provided the example name as `$ARGUMENTS` (snake_case).

## Steps

1. **Read one or two existing examples** (`examples/simple_chat.py`,
   `examples/agent_loop.py`) to match style: single `main()` function,
   `if __name__ == "__main__"` guard, `load_dotenv()` at the top.
2. **Ask the user what feature to demonstrate** if not clear from `$ARGUMENTS`.
3. **Write `examples/$ARGUMENTS.py`.**
   - Keep it under ~60 lines; a reader should understand it in 2 minutes.
   - Use `ClaudeClient` from `your_project_name.llm`, not the raw SDK.
   - Load credentials via `load_dotenv()` — never hard-code keys.
   - Add a one-paragraph docstring at the top: what it demonstrates and
     how to run it.
4. **Run the script** to confirm it executes without error:
   ```bash
   python examples/$ARGUMENTS.py
   ```
   If `ANTHROPIC_API_KEY` is not set, stop and ask the user to set it
   rather than guessing.
5. **Update `README.md`** (Examples section) with one line describing the
   new script, if the README already lists examples.

## Constraints

- Do not add new dependencies beyond what is already in `pyproject.toml`.
- Examples are documentation, not production code — no need for tests,
  but the script must be runnable as-is.
