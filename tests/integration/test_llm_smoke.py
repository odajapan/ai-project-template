"""Smoke test against the real Anthropic API.

Billable — run only with explicit human confirmation:

    pytest tests/integration -m integration -v

Skips itself when ANTHROPIC_API_KEY is not set.
"""

from __future__ import annotations

import os

import pytest

pytestmark = pytest.mark.integration


@pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set",
)
def test_chat_round_trip() -> None:
    from your_project_name.llm import ClaudeClient

    client = ClaudeClient(max_tokens=32)
    reply = client.chat("Reply with the single word PONG.")
    assert reply.strip()
