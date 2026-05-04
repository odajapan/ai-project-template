---
paths:
  - "src/**/llm.py"
  - "src/**/*client*.py"
  - "tests/**/test_*llm*.py"
---

# Claude API Development Rules

## Prompt Caching

- Cache system messages over 1 KB using `cache_control={"type": "ephemeral"}`
- Verify cache hits via `message.usage.cache_read_input_tokens`
- `ClaudeClient` handles caching automatically — do not bypass it

## Tool Use

- Define tools as Pydantic models in `schemas.py` and convert with `.to_tool()`
- Always handle `tool_use` blocks before `text` blocks in responses
- Return tool results in a follow-up user message, not as a system message

## Streaming

- Use `stream_chat()` for responses expected to exceed ~200 tokens
- Always consume the full stream — partial reads leave the connection open

## Error Handling

- Catch `anthropic.RateLimitError` and apply exponential backoff
- Log `input_tokens`, `output_tokens`, and cache stats on every call

## Testing

- Mock `anthropic.Anthropic` for unit tests — never hit the real API
- Track `cache_read_input_tokens` in tests that verify caching behaviour
- Integration tests (real API) live in `tests/integration/` and are skipped in CI
