"""Tests for the Claude API wrapper (llm.py).

All tests use mocks so no real API calls are made and no ANTHROPIC_API_KEY
is required when running the test suite.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture()
def mock_anthropic(monkeypatch: pytest.MonkeyPatch) -> MagicMock:
    """Patch ``anthropic.Anthropic`` before ClaudeClient is instantiated."""
    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_module.Anthropic.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_module)
    return mock_client


def _make_message(text: str) -> SimpleNamespace:
    block = SimpleNamespace(type="text", text=text)
    return SimpleNamespace(content=[block])


def test_chat_returns_text(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _make_message("Hello!")

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient()
    result = client.chat("Say hello.")

    assert result == "Hello!"
    mock_anthropic.messages.create.assert_called_once()


def test_chat_includes_system_with_cache_control(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _make_message("ok")

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient(system="You are a helpful assistant.")
    client.chat("Hi")

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert "system" in call_kwargs
    assert call_kwargs["system"][0]["cache_control"] == {"type": "ephemeral"}


def test_chat_no_system_omits_system_key(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = _make_message("ok")

    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient()
    client.chat("Hi")

    call_kwargs = mock_anthropic.messages.create.call_args.kwargs
    assert "system" not in call_kwargs


def test_missing_anthropic_raises_import_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import sys

    monkeypatch.delitem(sys.modules, "anthropic", raising=False)

    builtins_obj = __builtins__
    original_import = (  # type: ignore[union-attr]
        builtins_obj.__import__  # type: ignore[union-attr]
        if hasattr(builtins_obj, "__import__")
        else __import__
    )

    def raise_on_anthropic(name: str, *args: object, **kwargs: object) -> object:
        if name == "anthropic":
            raise ImportError("No module named 'anthropic'")
        return original_import(name, *args, **kwargs)  # type: ignore[call-arg]

    with patch("builtins.__import__", side_effect=raise_on_anthropic):
        import importlib

        import your_project_name.llm as llm_mod

        importlib.reload(llm_mod)

        with pytest.raises(ImportError, match="pip install"):
            llm_mod.ClaudeClient()
