---
name: claude-sdk
description: Patterns for using ClaudeClient correctly — caching, streaming, tool use, multi-turn, error handling.
---

# ClaudeClient usage patterns

Reference for working with `src/your_project_name/llm.py`.

## When to use which method

| Task | Method |
|---|---|
| Single Q&A, short response | `client.chat(prompt)` |
| Response likely > 200 tokens | `client.stream_chat(prompt)` |
| Tool use (function calling) | `client.chat_with_tools(prompt, tools)` |
| Multi-turn conversation | `client.chat(prompt, conversation_history=history)` |

## Caching

System messages over 1 KB are automatically cached by `ClaudeClient`.
Verify cache hits in tests:

```python
assert response.usage.cache_read_input_tokens > 0
```

Do not bypass `ClaudeClient` to call `anthropic.Anthropic` directly —
caching and tracking are built into the wrapper.

## Tool use pattern

```python
from your_project_name.schemas import ToolDefinition
from your_project_name.llm import ClaudeClient

tool = ToolDefinition(
    name="get_weather",
    description="Get current weather for a city",
    parameters={"city": {"type": "string"}},
)
client = ClaudeClient()
response = client.chat_with_tools("What's the weather in Tokyo?", tools=[tool])

# Always process tool_use blocks before text blocks
for block in response.content:
    if block.type == "tool_use":
        result = handle_tool_call(block.name, block.input)
```

## Error handling

```python
import anthropic

try:
    response = client.chat(prompt)
except anthropic.RateLimitError:
    # Exponential backoff — do not retry immediately
    time.sleep(backoff)
```

Log `input_tokens`, `output_tokens`, and cache stats on every call.
`ClaudeClient.chat_with_tracking()` does this automatically.

## Testing rules

- **Always mock `anthropic.Anthropic`** in unit tests — no real API calls.
- Use `unittest.mock.patch("your_project_name.llm.anthropic.Anthropic")`.
- Integration tests (real API) go in `tests/integration/` and are skipped
  by `make test`.

```python
from unittest.mock import MagicMock, patch

@patch("your_project_name.llm.anthropic.Anthropic")
def test_chat(mock_anthropic):
    mock_client = MagicMock()
    mock_anthropic.return_value = mock_client
    mock_client.messages.create.return_value = MagicMock(
        content=[MagicMock(type="text", text="hello")],
        usage=MagicMock(input_tokens=10, output_tokens=5,
                        cache_read_input_tokens=0, cache_creation_input_tokens=0),
    )
    client = ClaudeClient()
    assert "hello" in client.chat("hi")
```
