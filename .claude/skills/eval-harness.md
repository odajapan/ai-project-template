---
name: eval-harness
description: Patterns for testing LLM outputs — deterministic checks, LLM-as-judge, golden set regression, and pytest integration.
---

# LLM evaluation patterns

Standard `assert output == expected` breaks for LLM outputs because responses
are non-deterministic and semantically equivalent outputs look textually
different. Use a layered approach.

## Layer 1 — Deterministic checks (always do these)

Test everything that CAN be asserted exactly:

```python
def test_structured_output():
    result = parse_response(mock_response("some json"))
    assert isinstance(result, MySchema)        # type
    assert result.name != ""                   # non-empty
    assert result.score >= 0                   # range
    assert "error" not in result.tags          # absence
```

Format, schema validity, presence/absence of key terms, numeric ranges,
response length bounds — all deterministic.

## Layer 2 — Heuristic checks

For free-text, check proxies that correlate with quality:

```python
def test_summary_quality():
    summary = mock_summarise(LONG_DOC)
    words = summary.split()
    assert 30 <= len(words) <= 150             # not too short/long
    assert any(kw in summary.lower()
               for kw in ["revenue", "growth", "q3"])  # key concepts present
    assert summary.count("\n\n") <= 2          # not fragmented
```

## Layer 3 — LLM-as-judge (for semantic correctness)

Use a second Claude call to grade the first. Keep judge prompts in
`tests/prompts/` so they are versionable.

```python
JUDGE_PROMPT = """\
Rate the following answer on a scale 1-5 for factual accuracy.
Question: {question}
Answer: {answer}
Respond with JSON: {{"score": <int>, "reason": "<str>"}}"""

@pytest.mark.llm_judge
def test_answer_accuracy(real_client):
    answer = real_client.chat(QUESTION)
    verdict = real_client.chat(JUDGE_PROMPT.format(
        question=QUESTION, answer=answer))
    result = json.loads(verdict)
    assert result["score"] >= 4, result["reason"]
```

Mark judge tests with `@pytest.mark.llm_judge` and run separately — they
hit the real API and are slow/non-deterministic themselves.

## Layer 4 — Golden set regression

Maintain a small set of `(input, expected_keywords, forbidden_keywords)`
tuples in `tests/fixtures/golden.jsonl`. Run weekly or before a model
upgrade.

```python
@pytest.mark.golden
@pytest.mark.parametrize("case", load_golden())
def test_golden(case, real_client):
    output = real_client.chat(case["input"])
    for kw in case["must_contain"]:
        assert kw.lower() in output.lower(), f"missing: {kw}"
    for kw in case["must_not_contain"]:
        assert kw.lower() not in output.lower(), f"found forbidden: {kw}"
```

## pytest marks setup (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
markers = [
    "llm_judge: requires real API, grades with a second LLM call",
    "golden: golden set regression, run before model upgrades",
    "integration: real API call, skipped in CI",
]
```

`make test` runs none of the marked tests. Run them manually:
```bash
pytest -m llm_judge
pytest -m golden
```

## What belongs in unit tests (mocked)

- Prompt construction (assert the right variables are interpolated)
- Response parsing (valid / malformed / empty)
- Retry logic and error handling
- Token counting and caching behaviour
