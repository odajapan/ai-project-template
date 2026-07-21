# Integration tests

Tests in this directory hit the **real Anthropic API** and are billable.

They are excluded from the default test run twice over:

- `norecursedirs = ["tests/integration"]` in `pyproject.toml`
- the default marker filter `-m 'not llm_judge and not golden and not integration'`

So `make test` / `make check` / CI never run them.

## Running

Requires `ANTHROPIC_API_KEY` (via `.env` or the environment) and — per
`AGENTS.md` — **explicit confirmation from a human** before running,
since real API calls are billable:

```bash
pytest tests/integration -m integration -v
```

Tests skip themselves when `ANTHROPIC_API_KEY` is not set, so the
command is safe to run in a key-less environment (everything reports
as skipped).

## Writing integration tests

- Mark every test with `@pytest.mark.integration`
- Guard on the API key with `pytest.mark.skipif`
- Keep prompts tiny (`max_tokens` low) — these are smoke tests, not evals
- For output-quality checks (LLM-as-judge, golden sets), use the
  `llm_judge` / `golden` markers instead — see the `eval-harness` skill
