"""Shared fixtures and response builders for the test suite.

The ``mock_anthropic`` fixture replaces the ``anthropic`` module in
``sys.modules`` *before* any ``ClaudeClient`` is instantiated, so the
lazy ``import anthropic`` inside ``llm.py`` picks up the mock. No real
API calls, no ANTHROPIC_API_KEY required.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest


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
    mock_module.APIError = type("APIError", (Exception,), {})
    mock_module.RateLimitError = type("RateLimitError", (Exception,), {})
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_module)
    return mock_client
