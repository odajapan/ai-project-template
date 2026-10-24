---
name: python-testing
description: pytest conventions, mock patterns, and coverage rules for this project.
---

# Python testing conventions

Reference for writing and running tests in `tests/`.

## File layout

```
tests/
  test_cli.py          # Click CLI commands
  test_llm.py          # ClaudeClient (all mocked)
  test_utils.py        # Pure utility helpers
  test_tools.py        # ToolDefinition + handlers (create if adding tools)
  integration/         # Real-API tests — skipped by make test
    test_llm_live.py
```

Mirror `src/your_project_name/<module>.py` → `tests/test_<module>.py`.

## Running tests

```bash
make test                          # all unit tests (no real API)
make check                         # lint + typecheck + tests
pytest tests/test_llm.py -x -q    # single file, stop on first fail
pytest -k "test_chat" -x -q       # single test by name
pytest --cov=src --cov-report=term-missing  # coverage report
```

## Mock pattern for ClaudeClient

`llm.py` imports `anthropic` **lazily** inside `_make_client()`, so
`@patch("your_project_name.llm.anthropic.Anthropic")` raises `AttributeError`.
Use `monkeypatch.setitem(sys.modules, ...)` instead — exactly as
`tests/test_llm.py` does:

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

def test_something(mock_anthropic: MagicMock) -> None:
    mock_anthropic.messages.create.return_value = SimpleNamespace(
        content=[SimpleNamespace(type="text", text="expected output")],
        usage=SimpleNamespace(
            input_tokens=10, output_tokens=5,
            cache_read_input_tokens=0, cache_creation_input_tokens=0,
        ),
    )
    from your_project_name.llm import ClaudeClient
    result = ClaudeClient().chat("prompt")
    assert "expected output" in result
```

## What every public function needs

- At least one happy-path test.
- One test for the primary error case (invalid input, missing key, etc.)
- If the function calls Claude: mock it; never hit the real API.

## Integration tests

Place in `tests/integration/`, mark with `@pytest.mark.integration`:

```python
import pytest

@pytest.mark.integration
def test_real_api():
    ...
```

`pytest.ini` / `pyproject.toml` excludes `integration/` from default runs.
Run manually with `pytest tests/integration/ -m integration`.

## Coverage target

`make check` does not enforce a hard coverage floor, but aim for > 80%
on `src/`. Check with:

```bash
pytest --cov=src --cov-report=term-missing --cov-fail-under=80
```
