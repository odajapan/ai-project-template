---
paths:
  - "tests/**"
  - "src/**"
---

# Testing Rules

## Structure

- Mirror `src/` layout under `tests/` (e.g. `src/foo/bar.py` → `tests/foo/test_bar.py`)
- One test file per source module
- Integration tests go in `tests/integration/` and are excluded from `make test`

## Standards

- All public functions require at least one test
- Test both the happy path and the main error/edge cases
- Use `pytest.fixture` for shared setup — no copy-pasted setup code

## Mocking

- Mock at system boundaries only: external APIs, file I/O, DB calls
- Do not mock internal project functions
- Use `monkeypatch` for environment variables and module-level state

## Naming

- Test functions: `test_<what>_<condition>` (e.g. `test_slugify_strips_special_chars`)
- Fixtures: noun phrases describing what they provide (e.g. `mock_anthropic`, `tmp_csv`)

## Commands

```bash
make test              # unit tests only
pytest tests/ -x -q    # stop on first failure
pytest tests/ --cov=src --cov-report=term-missing  # with coverage
```
