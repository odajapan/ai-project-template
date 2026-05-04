"""Claude API wrapper with prompt caching.

Provides a project-friendly interface around the Anthropic SDK.
All public classes share the same configuration surface and respect the
``ANTHROPIC_API_KEY`` / ``CLAUDE_MODEL`` environment variables.

Quick start::

    from your_project_name.llm import ClaudeClient

    client = ClaudeClient(system="You are a helpful data analyst.")
    print(client.chat("Summarise this dataset in one sentence."))

Streaming::

    for chunk in client.stream_chat("Tell me a long story."):
        print(chunk, end="", flush=True)

Tool use::

    from your_project_name.schemas import ToolDefinition

    tools = [ToolDefinition(name="get_weather", description="...", input_schema={...})]
    text, tool_calls = client.chat_with_tools("What's the weather?", tools=tools)

Multi-turn conversation::

    conv = ConversationClient()
    conv.send("Hello!")
    conv.send("What did I just say?")
    conv.reset()

Token usage tracking::

    text, usage = client.chat_with_tracking("Hello")
    print(usage["cache_read_input_tokens"])
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from typing import Any

DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
DEFAULT_MAX_TOKENS = 1024


class UsageStats:
    """Token usage snapshot returned by ``chat_with_tracking``."""

    def __init__(self, raw: Any) -> None:
        self.input_tokens: int = getattr(raw, "input_tokens", 0)
        self.output_tokens: int = getattr(raw, "output_tokens", 0)
        self.cache_creation_input_tokens: int = getattr(
            raw, "cache_creation_input_tokens", 0
        )
        self.cache_read_input_tokens: int = getattr(raw, "cache_read_input_tokens", 0)

    def as_dict(self) -> dict[str, int]:
        return {
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
            "cache_read_input_tokens": self.cache_read_input_tokens,
        }


class ClaudeClient:
    """Single-turn Claude client with prompt caching and optional tool use."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        system: str = "",
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        self._client = self._make_client()
        self.model = model
        self.system = system
        self.max_tokens = max_tokens

    @staticmethod
    def _make_client() -> Any:
        try:
            import anthropic  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required. "
                "Install it with: pip install -e .[claude]"
            ) from exc
        return anthropic.Anthropic()

    def _system_blocks(self) -> list[dict[str, Any]]:
        if not self.system:
            return []
        return [
            {
                "type": "text",
                "text": self.system,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def _base_kwargs(self, messages: list[dict[str, Any]]) -> dict[str, Any]:
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": list(messages),
        }
        system_blocks = self._system_blocks()
        if system_blocks:
            kwargs["system"] = system_blocks
        return kwargs

    @staticmethod
    def _extract_text(message: Any) -> str:
        for block in message.content:
            if block.type == "text":
                return str(block.text)
        return ""

    # ------------------------------------------------------------------
    # Single-turn helpers
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Send a single message and return the text response."""
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        return self._extract_text(self._client.messages.create(**kwargs))

    def chat_with_tracking(self, user_message: str) -> tuple[str, dict[str, int]]:
        """Like ``chat`` but also returns token usage statistics."""
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        message = self._client.messages.create(**kwargs)
        return self._extract_text(message), UsageStats(message.usage).as_dict()

    def chat_with_tools(
        self,
        user_message: str,
        tools: list[Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]]]:
        """Send a message with optional tool definitions.

        Returns ``(response_text, tool_calls)`` where *tool_calls* is a list
        of ``{"name": ..., "input": ...}`` dicts for every tool the model
        invoked.
        """
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        if tools:
            kwargs["tools"] = [
                t.to_tool() if hasattr(t, "to_tool") else t for t in tools
            ]
        message = self._client.messages.create(**kwargs)
        tool_calls = [
            {"name": block.name, "input": block.input}
            for block in message.content
            if block.type == "tool_use"
        ]
        return self._extract_text(message), tool_calls

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def stream_chat(self, user_message: str) -> Iterator[str]:
        """Yield response text in chunks as they arrive."""
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        with self._client.messages.stream(**kwargs) as stream:
            yield from stream.text_stream

    # ------------------------------------------------------------------
    # Extended thinking  (requires a thinking-capable model)
    # ------------------------------------------------------------------

    def chat_with_thinking(
        self,
        user_message: str,
        budget_tokens: int = 5000,
    ) -> tuple[str, str]:
        """Return ``(thinking, response)`` using extended thinking.

        Pass a model that supports extended thinking, e.g.
        ``ClaudeClient(model="claude-opus-4-7")``.
        """
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        kwargs["thinking"] = {"type": "enabled", "budget_tokens": budget_tokens}
        kwargs["max_tokens"] = max(self.max_tokens, budget_tokens + 512)

        message = self._client.messages.create(**kwargs)

        thinking_text = ""
        response_text = ""
        for block in message.content:
            if block.type == "thinking":
                thinking_text = str(block.thinking)
            elif block.type == "text":
                response_text = str(block.text)
        return thinking_text, response_text


class ConversationClient(ClaudeClient):
    """Multi-turn client that maintains conversation history in memory."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._history: list[dict[str, Any]] = []

    def send(self, user_message: str) -> str:
        """Append *user_message* to history, call the API, store the reply."""
        self._history.append({"role": "user", "content": user_message})
        kwargs = self._base_kwargs(self._history)
        message = self._client.messages.create(**kwargs)
        reply = self._extract_text(message)
        self._history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        """Clear conversation history."""
        self._history = []

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)
