# Examples

Runnable scripts that show how to use the project's Claude API helpers.
Each script is self-contained and can be run directly:

```bash
python examples/simple_chat.py
python examples/agent_loop.py
python examples/structured_extraction.py
```

All examples expect `ANTHROPIC_API_KEY` to be set (see `env.example`).

| Script | Demonstrates |
|--------|--------------|
| `simple_chat.py` | Basic single-turn chat with cached system prompt + token usage |
| `agent_loop.py` | Tool use: Claude calls a tool, you execute it, return the result |
| `structured_extraction.py` | Parse Claude's JSON output into a Pydantic model |
