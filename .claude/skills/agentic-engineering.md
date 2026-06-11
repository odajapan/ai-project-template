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
    input_schema={
        "type": "object",
        "properties": {"query": {"type": "string", "description": "search term"}},
        "required": ["query"],
    },
)

# 2. chat_with_tools returns (text, tool_calls) — a tuple, not a message object
text, tool_calls = client.chat_with_tools(prompt, tools=[tool])

for call in tool_calls:
    result = dispatch(call["name"], call["input"])
    # Feed results back via continue_with_tool_results
```

**Description quality is the #1 lever.** A vague description → the model
calls the wrong tool or skips it entirely. Include: what it does, when to
use it, what it returns.

## Agent loop skeleton

`chat_with_tools` is single-turn. For multi-step tool use, call
`continue_with_tool_results` to feed results back, then repeat.

```python
MAX_TURNS = 10
user_message = prompt

for _ in range(MAX_TURNS):
    text, tool_calls = client.chat_with_tools(user_message, tools=tools)

    if not tool_calls:
        break  # model finished without requesting more tools

    # Reconstruct assistant_content shape expected by the Anthropic API
    assistant_content = [
        {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["input"]}
        for c in tool_calls
    ]
    tool_results = [
        {"tool_use_id": c["id"], "content": dispatch(c["name"], c["input"])}
        for c in tool_calls
    ]
    # continue_with_tool_results sends a fresh three-turn context each call.
    # For true history accumulation across many turns use ConversationClient
    # and manage tool_use / tool_result blocks manually.
    text = client.continue_with_tool_results(
        user_message=user_message,
        assistant_content=assistant_content,
        tool_results=tool_results,
        tools=tools,
    )
    user_message = text  # carry forward for next turn
```

Cap `MAX_TURNS` (10–20). An unbounded loop is a runaway cost risk.

## Structured output without tool use

```python
from your_project_name.schemas import StructuredResponse

class MySummary(StructuredResponse):
    title: str
    key_points: list[str]

prompt = f"""
Respond ONLY with valid JSON matching this schema:
{MySummary.model_json_schema()}

Input: {user_input}
"""
raw = client.chat(prompt)
result = MySummary.from_text(raw)   # StructuredResponse.from_text parses JSON
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
