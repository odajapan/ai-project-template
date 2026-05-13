"""Tests for llm.py and schemas.py.

All tests use mocks — no real API calls, no ANTHROPIC_API_KEY required.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _text_block(text: str) -> SimpleNamespace:
    return SimpleNamespace(type="text", text=text)


def _tool_block(name: str, inp: dict, tool_id: str = "tool_abc") -> SimpleNamespace:
    return SimpleNamespace(type="tool_use", id=tool_id, name=name, input=inp)


def _thinking_block(thinking: str) -> SimpleNamespace:
    return SimpleNamespace(type="thinking", thinking=thinking)


def _message(*blocks: SimpleNamespace, usage: object | None = None) -> SimpleNamespace:
    if usage is None:
        usage = SimpleNamespace(
            input_tokens=10,
            output_tokens=5,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        )
    return SimpleNamespace(content=list(blocks), usage=usage)


@pytest.fixture()
def mock_anthropic(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch ``anthropic.Anthropic`` before any ClaudeClient is instantiated."""
    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_module.Anthropic.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_module)
    return mock_client


# ---------------------------------------------------------------------------
# ClaudeClient.chat
# ---------------------------------------------------------------------------


def test_chat_returns_text(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("Hello!"))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    assert ClaudeClient().chat("Hi") == "Hello!"


def test_chat_with_system_adds_cache_control(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    ClaudeClient(system="You are helpful.").chat("Hi")
    kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_chat_no_system_omits_system_key(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    ClaudeClient().chat("Hi")
    assert "system" not in mock_anthropic.messages.create.call_args.kwargs


# ---------------------------------------------------------------------------
# ClaudeClient.chat_with_tracking
# ---------------------------------------------------------------------------


def test_chat_with_tracking_returns_usage(mock_anthropic: MagicMock) -> None:
    usage = SimpleNamespace(
        input_tokens=20,
        output_tokens=8,
        cache_creation_input_tokens=15,
        cache_read_input_tokens=5,
    )
    mock_anthropic.messages.create.return_value = _message(
        _text_block("ok"), usage=usage
    )

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    text, stats = ClaudeClient().chat_with_tracking("Hi")
    assert text == "ok"
    assert stats["input_tokens"] == 20
    assert stats["cache_read_input_tokens"] == 5


# ---------------------------------------------------------------------------
# ClaudeClient.chat_with_tools
# ---------------------------------------------------------------------------


def test_chat_with_tools_returns_tool_calls(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(
        _text_block("Checking weather..."),
        _tool_block("get_weather", {"city": "Tokyo"}, tool_id="tool_001"),
    )

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    _, calls = ClaudeClient().chat_with_tools("Weather in Tokyo?")
    assert calls == [
        {"id": "tool_001", "name": "get_weather", "input": {"city": "Tokyo"}}
    ]


def test_continue_with_tool_results_sends_tool_result_block(
    mock_anthropic: MagicMock,
) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("Sunny, 22C."))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    assistant_content = [_tool_block("get_weather", {"city": "Tokyo"}, "tool_42")]
    reply = ClaudeClient().continue_with_tool_results(
        user_message="Weather in Tokyo?",
        assistant_content=assistant_content,
        tool_results=[{"tool_use_id": "tool_42", "content": "Sunny, 22C"}],
    )
    assert reply == "Sunny, 22C."
    messages = mock_anthropic.messages.create.call_args.kwargs["messages"]
    assert messages[-1]["role"] == "user"
    assert messages[-1]["content"][0]["type"] == "tool_result"
    assert messages[-1]["content"][0]["tool_use_id"] == "tool_42"


def test_chat_with_tools_passes_tool_definitions(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415
    from your_project_name.schemas import ToolDefinition  # noqa: PLC0415

    tool = ToolDefinition(
        name="ping",
        description="Ping a host.",
        input_schema={"type": "object", "properties": {"host": {"type": "string"}}},
    )
    ClaudeClient().chat_with_tools("Ping example.com", tools=[tool])
    kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert kwargs["tools"][0]["name"] == "ping"


def test_chat_with_no_tools_omits_tools_key(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    ClaudeClient().chat_with_tools("Hi")
    assert "tools" not in mock_anthropic.messages.create.call_args.kwargs


# ---------------------------------------------------------------------------
# ClaudeClient.stream_chat
# ---------------------------------------------------------------------------


def test_stream_chat_yields_chunks(mock_anthropic: MagicMock) -> None:
    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = iter(["Hello", ", ", "world!"])
    mock_anthropic.messages.stream.return_value = mock_stream

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    chunks = list(ClaudeClient().stream_chat("Hi"))
    assert "".join(chunks) == "Hello, world!"


# ---------------------------------------------------------------------------
# ClaudeClient.chat_with_thinking
# ---------------------------------------------------------------------------


def test_chat_with_thinking_returns_thinking_and_text(
    mock_anthropic: MagicMock,
) -> None:
    mock_anthropic.messages.create.return_value = _message(
        _thinking_block("I should say hello."),
        _text_block("Hello!"),
    )

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    thinking, response = ClaudeClient().chat_with_thinking("Hi")
    assert thinking == "I should say hello."
    assert response == "Hello!"


def test_chat_with_thinking_sets_thinking_param(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    ClaudeClient().chat_with_thinking("Hi", budget_tokens=3000)
    kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert kwargs["thinking"] == {"type": "enabled", "budget_tokens": 3000}


def test_chat_concatenates_multiple_text_blocks(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(
        _text_block("Hello, "),
        _tool_block("noop", {}),
        _text_block("world!"),
    )

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    assert ClaudeClient().chat("Hi") == "Hello, world!"


def test_chat_with_thinking_concatenates_multiple_blocks(
    mock_anthropic: MagicMock,
) -> None:
    mock_anthropic.messages.create.return_value = _message(
        _thinking_block("first thought; "),
        _thinking_block("second thought"),
        _text_block("answer A "),
        _text_block("answer B"),
    )

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    thinking, response = ClaudeClient().chat_with_thinking("Hi")
    assert thinking == "first thought; second thought"
    assert response == "answer A answer B"


# ---------------------------------------------------------------------------
# ConversationClient
# ---------------------------------------------------------------------------


def test_conversation_accumulates_history(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("Hi there!"))

    from your_project_name.llm import ConversationClient  # noqa: PLC0415

    conv = ConversationClient()
    conv.send("Hello")
    assert len(conv.history) == 2
    assert conv.history[0] == {"role": "user", "content": "Hello"}
    assert conv.history[1] == {"role": "assistant", "content": "Hi there!"}


def test_conversation_reset_clears_history(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ConversationClient  # noqa: PLC0415

    conv = ConversationClient()
    conv.send("Hello")
    conv.reset()
    assert conv.history == []


def test_conversation_sends_full_history(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _message(_text_block("ok"))

    from your_project_name.llm import ConversationClient  # noqa: PLC0415

    conv = ConversationClient()
    conv.send("First")
    conv.send("Second")
    last_messages = mock_anthropic.messages.create.call_args.kwargs["messages"]
    assert len(last_messages) == 3  # user, assistant, user


# ---------------------------------------------------------------------------
# Missing anthropic package
# ---------------------------------------------------------------------------


def test_missing_anthropic_raises_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib
    import sys

    import your_project_name.llm as llm_mod

    monkeypatch.delitem(sys.modules, "anthropic", raising=False)

    _real_import = __import__

    def _raise(name: str, *args: object, **kwargs: object) -> object:
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return _real_import(name, *args, **kwargs)  # type: ignore[call-arg]

    with patch("builtins.__import__", side_effect=_raise):
        importlib.reload(llm_mod)
        with pytest.raises(ImportError, match="pip install"):
            llm_mod.ClaudeClient()


# ---------------------------------------------------------------------------
# ToolDefinition / StructuredResponse (schemas.py)
# ---------------------------------------------------------------------------


def test_tool_definition_to_tool() -> None:
    from your_project_name.schemas import ToolDefinition  # noqa: PLC0415

    tool = ToolDefinition(
        name="ping",
        description="Ping.",
        input_schema={"type": "object"},
    )
    assert tool.to_tool() == {
        "name": "ping",
        "description": "Ping.",
        "input_schema": {"type": "object"},
    }


def test_structured_response_from_text() -> None:
    from your_project_name.schemas import StructuredResponse  # noqa: PLC0415

    class Summary(StructuredResponse):
        title: str
        score: float

    result = Summary.from_text('{"title": "Test", "score": 0.9}')
    assert result.title == "Test"
    assert result.score == pytest.approx(0.9)
