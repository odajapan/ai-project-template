---
name: "source-command-debug"
description: "Systematically diagnose and fix a Python error or failing test. Paste the traceback or test output as the argument."
---

# source-command-debug

Use this skill when the user asks to run the migrated source command `debug`.
`$ARGUMENTS` below stands for the argument the user gave with the request.

## Command Template

# /debug — diagnose and fix a Python error

Given the error output in `$ARGUMENTS`, find and fix the root cause.

## Steps

1. **Parse the traceback.** Identify the innermost failing file and line.
   Read that function and its immediate callers.
2. **Form one hypothesis.** State it in one sentence before touching anything.
   Common causes in this codebase:
   - Missing mock for `anthropic.Anthropic` in a unit test
   - Type mismatch (check mypy output: `make typecheck`)
   - Import error after a rename — grep for the old name
   - `ANTHROPIC_API_KEY` not set when running a non-mocked test
3. **Verify the hypothesis cheaply.** Run the single failing test:
   ```bash
   pytest tests/test_<module>.py::test_<name> -x -q
   ```
4. **Apply the minimal fix.** Do not refactor surrounding code.
5. **Run `make check`.** All 3 stages (lint + typecheck + tests) must be green
   before declaring done.
6. If the fix requires touching more than 2 files, stop and describe the
   full scope to the user before continuing.

## What not to do

- Do not add `# type: ignore` to silence mypy — fix the type.
- Do not add `try/except` around the error unless the error is genuinely
  expected at a boundary (user input, external API).
- Do not call the real Anthropic API in tests — mock it.
