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
| Multi-turn conversation | `ConversationClient().send(prompt)` |

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
    input_schema={
        "type": "object",
        "properties": {"city": {"type": "string"}},
        "required": ["city"],
    },
)
client = ClaudeClient()

# chat_with_tools returns (text, tool_calls) — a tuple, not a message object
text, tool_calls = client.chat_with_tools("What's the weather in Tokyo?", tools=[tool])

for call in tool_calls:
    result = handle_tool_call(call["name"], call["input"])
    # Feed results back with continue_with_tool_results
    assistant_content = [
        {"type": "tool_use", "id": c["id"], "name": c["name"], "input": c["input"]}
        for c in tool_calls
    ]
    final = client.continue_with_tool_results(
        user_message="What's the weather in Tokyo?",
        assistant_content=assistant_content,
        tool_results=[{"tool_use_id": call["id"], "content": result}],
        tools=[tool],
    )
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

- **Always mock `anthropic`** in unit tests — no real API calls.
- `llm.py` imports `anthropic` lazily inside `_make_client()`, so
  `patch("your_project_name.llm.anthropic.Anthropic")` **does not work**.
  Use `monkeypatch.setitem(sys.modules, "anthropic", mock_module)` instead
  (exactly as `tests/test_llm.py` does).
- Integration tests (real API) go in `tests/integration/` and are skipped
  by `make test`.

```python
from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest

@pytest.fixture()
def mock_anthropic(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_module.Anthropic.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_module)
    return mock_client

def test_chat(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="hello")],
        usage=SimpleNamespace(input_tokens=10, output_tokens=5,
                              cache_read_input_tokens=0, cache_creation_input_tokens=0),
    )
    from your_project_name.llm import ClaudeClient
    assert "hello" in ClaudeClient().chat("hi")
```
