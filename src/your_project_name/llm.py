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
    text, tool_calls, content = client.chat_with_tools("Weather?", tools=tools)

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

from your_project_name.exceptions import LLMError

DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5")
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
            import anthropic
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
        return "".join(
            str(block.text) for block in message.content if block.type == "text"
        )

    def _call_api(self, fn: Any, **kwargs: Any) -> Any:
        """Call an anthropic messages function, re-raising SDK errors as LLMError."""
        import anthropic

        try:
            return fn(**kwargs)
        except anthropic.APIError as e:
            raise LLMError(str(e)) from e

    # ------------------------------------------------------------------
    # Single-turn helpers
    # ------------------------------------------------------------------

    def chat(self, user_message: str) -> str:
        """Send a single message and return the text response."""
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        return self._extract_text(
            self._call_api(self._client.messages.create, **kwargs)
        )

    def chat_with_tracking(self, user_message: str) -> tuple[str, dict[str, int]]:
        """Like ``chat`` but also returns token usage statistics."""
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        message = self._call_api(self._client.messages.create, **kwargs)
        return self._extract_text(message), UsageStats(message.usage).as_dict()

    def chat_with_tools(
        self,
        user_message: str,
        tools: list[Any] | None = None,
    ) -> tuple[str, list[dict[str, Any]], list[Any]]:
        """Send a message with optional tool definitions.

        Returns ``(response_text, tool_calls, assistant_content)``.
        *tool_calls* is a list of ``{"id": ..., "name": ..., "input": ...}``
        dicts for every tool the model invoked; the ``id`` is the
        ``tool_use_id`` that must be referenced when returning the tool
        result. *assistant_content* is the raw ``message.content`` — pass it
        unchanged to ``continue_with_tool_results`` for the follow-up turn.
        """
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        if tools:
            kwargs["tools"] = [
                t.to_tool() if hasattr(t, "to_tool") else t for t in tools
            ]
        message = self._call_api(self._client.messages.create, **kwargs)
        tool_calls = [
            {"id": block.id, "name": block.name, "input": block.input}
            for block in message.content
            if block.type == "tool_use"
        ]
        return self._extract_text(message), tool_calls, list(message.content)

    def continue_with_tool_results(
        self,
        user_message: str,
        assistant_content: list[Any],
        tool_results: list[dict[str, Any]],
        tools: list[Any] | None = None,
    ) -> str:
        """Send a follow-up turn with tool_result blocks.

        *assistant_content* is the raw ``message.content`` returned from the
        previous turn (containing ``tool_use`` blocks). *tool_results* is a
        list of ``{"tool_use_id": ..., "content": ...}`` mappings.
        """
        kwargs = self._base_kwargs(
            [
                {"role": "user", "content": user_message},
                {"role": "assistant", "content": assistant_content},
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": r["tool_use_id"],
                            "content": r["content"],
                        }
                        for r in tool_results
                    ],
                },
            ]
        )
        if tools:
            kwargs["tools"] = [
                t.to_tool() if hasattr(t, "to_tool") else t for t in tools
            ]
        return self._extract_text(
            self._call_api(self._client.messages.create, **kwargs)
        )

    # ------------------------------------------------------------------
    # Streaming
    # ------------------------------------------------------------------

    def stream_chat(self, user_message: str) -> Iterator[str]:
        """Yield response text in chunks as they arrive."""
        import anthropic

        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        try:
            with self._client.messages.stream(**kwargs) as stream:
                yield from stream.text_stream
        except anthropic.APIError as e:
            raise LLMError(str(e)) from e

    # ------------------------------------------------------------------
    # Adaptive thinking  (requires an adaptive-thinking model)
    # ------------------------------------------------------------------

    def chat_with_thinking(
        self,
        user_message: str,
        effort: str | None = None,
    ) -> tuple[str, str]:
        """Return ``(thinking, response)`` using adaptive thinking.

        Requires an adaptive-thinking model — the default
        ``claude-sonnet-5`` qualifies, as do ``claude-opus-4-8`` and later.
        ``display: "summarized"`` is set explicitly because those models
        default to ``"omitted"``, which returns thinking blocks with empty
        text. *effort* optionally sets ``output_config.effort``
        ("low" | "medium" | "high" | "xhigh" | "max").
        """
        kwargs = self._base_kwargs([{"role": "user", "content": user_message}])
        kwargs["thinking"] = {"type": "adaptive", "display": "summarized"}
        if effort:
            kwargs["output_config"] = {"effort": effort}
        # Thinking spends from max_tokens; the 1024 default is too tight.
        kwargs["max_tokens"] = max(self.max_tokens, 8192)

        message = self._call_api(self._client.messages.create, **kwargs)

        thinking_parts: list[str] = []
        response_parts: list[str] = []
        for block in message.content:
            if block.type == "thinking":
                thinking_parts.append(str(block.thinking))
            elif block.type == "text":
                response_parts.append(str(block.text))
        return "".join(thinking_parts), "".join(response_parts)


class ConversationClient(ClaudeClient):
    """Multi-turn client that maintains conversation history in memory."""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._history: list[dict[str, Any]] = []

    def send(self, user_message: str) -> str:
        """Append *user_message* to history, call the API, store the reply."""
        self._history.append({"role": "user", "content": user_message})
        kwargs = self._base_kwargs(self._history)
        message = self._call_api(self._client.messages.create, **kwargs)
        reply = self._extract_text(message)
        self._history.append({"role": "assistant", "content": reply})
        return reply

    def reset(self) -> None:
        """Clear conversation history."""
        self._history = []

    @property
    def history(self) -> list[dict[str, Any]]:
        return list(self._history)
