"""Claude API wrapper with prompt caching.

Provides a thin, project-friendly interface around the Anthropic SDK.
Prompt caching is enabled by default for system prompts longer than 1024
tokens — this significantly reduces latency and cost on repeated calls.

Usage::

    from your_project_name.llm import ClaudeClient

    client = ClaudeClient()
    response = client.chat("Summarize this dataset in one sentence.")
    print(response)

Set ``ANTHROPIC_API_KEY`` in your environment (or ``.env``) before use.
"""

from __future__ import annotations

import os
from typing import Any

DEFAULT_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-6")
DEFAULT_MAX_TOKENS = 1024


class ClaudeClient:
    """Lightweight wrapper around ``anthropic.Anthropic`` with caching support."""

    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        system: str = "",
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> None:
        try:
            import anthropic  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError(
                "The 'anthropic' package is required. "
                "Install it with: pip install -e .[claude]"
            ) from exc

        self._client = anthropic.Anthropic()
        self.model = model
        self.system = system
        self.max_tokens = max_tokens

    def _system_blocks(self) -> list[dict[str, Any]]:
        """Return system content blocks with cache_control when text is present."""
        if not self.system:
            return []
        return [
            {
                "type": "text",
                "text": self.system,
                "cache_control": {"type": "ephemeral"},
            }
        ]

    def chat(self, user_message: str) -> str:
        """Send a single user message and return the text response."""
        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": [{"role": "user", "content": user_message}],
        }
        system_blocks = self._system_blocks()
        if system_blocks:
            kwargs["system"] = system_blocks

        message = self._client.messages.create(**kwargs)
        block = message.content[0]
        if block.type != "text":
            raise ValueError(f"Unexpected content block type: {block.type}")
        return block.text
