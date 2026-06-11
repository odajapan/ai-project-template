---
name: agentic-engineering
description: Patterns for building reliable Claude-based agents — tool use, agent loops, subagent delegation, structured output, and prompt design.
---

# Agentic engineering patterns

## Choosing the right pattern

| Goal | Pattern |
|---|---|
| Single structured answer | `chat()` + Pydantic output parsing |
| Use external functions | `chat_with_tools()` with `ToolDefinition` |
| Multi-step reasoning | Agent loop (tool call → result → next call) |
| Parallelisable subtasks | Subagents via Claude Code `Agent` tool |
| Long autonomous run | Subagents + stop conditions + human checkpoint |

## Tool use — the reliable pattern

```python
# 1. Define tools in schemas.py as Pydantic models
tool = ToolDefinition(
    name="search_docs",
    description="Search the project docs for a keyword.",  # be specific
    parameters={"query": {"type": "string", "description": "search term"}},
)

# 2. Always process tool_use before text in the response
for block in response.content:
    if block.type == "tool_use":
        result = dispatch(block.name, block.input)
        # Return result in follow-up user message, not system message
```

**Description quality is the #1 lever.** A vague description → the model
calls the wrong tool or skips it entirely. Include: what it does, when to
use it, what it returns.

## Agent loop skeleton

```python
history = []
for _ in range(MAX_TURNS):
    response = client.chat_with_tools(prompt, tools=tools, history=history)
    history.append({"role": "assistant", "content": response.content})

    tool_calls = [b for b in response.content if b.type == "tool_use"]
    if not tool_calls:
        break  # model is done

    results = [{"type": "tool_result", "tool_use_id": b.id,
                "content": dispatch(b.name, b.input)} for b in tool_calls]
    history.append({"role": "user", "content": results})
```

Cap `MAX_TURNS` (10–20). An unbounded loop is a runaway cost risk.

## Structured output without tool use

```python
from your_project_name.schemas import StructuredOutputModel

prompt = f"""
Respond ONLY with valid JSON matching this schema:
{StructuredOutputModel.model_json_schema()}

Input: {user_input}
"""
raw = client.chat(prompt)
result = StructuredOutputModel.model_validate_json(raw)
```

Prefer tool use over JSON-in-prompt for complex schemas — the model is
more reliable when given a typed interface.

## Subagent delegation (Claude Code)

Use the `Agent` tool to spin up a subagent for independent work:
- `explorer` (Haiku) for read-only lookups
- `implementer` (Sonnet) for edits + `make check`
- `code-reviewer` (Opus) for review before PR

Stop conditions belong in the subagent prompt, not assumed:
```
Stop and report if: the change exceeds 3 files, tests fail twice,
or any write to data/raw/ or .env* would be required.
```

## Prompt engineering rules

- **One instruction per sentence.** Long bullets are ignored.
- **State the output format explicitly.** "Return a JSON array of…"
- **Repeat the constraint at the end** of long prompts — models favour
  recency.
- **Give a worked example** for non-obvious formats.
- Never say "try to" or "attempt to" — be imperative.
