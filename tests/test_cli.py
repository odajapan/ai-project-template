from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner

from your_project_name.cli import cli


def test_cli_hello_default() -> None:
    result = CliRunner().invoke(cli, ["hello"])
    assert result.exit_code == 0
    assert "Hello, world!" in result.output


def test_cli_hello_name() -> None:
    result = CliRunner().invoke(cli, ["hello", "Alice"])
    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output


def test_ask_without_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    result = CliRunner().invoke(cli, ["ask", "hello"])
    assert result.exit_code != 0
    assert "ANTHROPIC_API_KEY" in result.output


def test_ask_streams_response(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_module.Anthropic.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_module)

    mock_stream = MagicMock()
    mock_stream.__enter__ = MagicMock(return_value=mock_stream)
    mock_stream.__exit__ = MagicMock(return_value=False)
    mock_stream.text_stream = iter(["Hello", " world"])
    mock_client.messages.stream.return_value = mock_stream

    result = CliRunner().invoke(cli, ["ask", "hi"])
    assert result.exit_code == 0
    assert "Hello world" in result.output


def test_ask_no_stream(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")

    mock_module = MagicMock()
    mock_client = MagicMock()
    mock_module.Anthropic.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_module)

    mock_client.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="42")],
        usage=SimpleNamespace(
            input_tokens=1,
            output_tokens=1,
            cache_creation_input_tokens=0,
            cache_read_input_tokens=0,
        ),
    )

    result = CliRunner().invoke(cli, ["ask", "--no-stream", "answer?"])
    assert result.exit_code == 0
    assert "42" in result.output
