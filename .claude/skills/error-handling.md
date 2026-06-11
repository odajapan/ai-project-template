---
name: error-handling
description: Python error handling conventions — where to validate, custom exceptions, retry patterns, and error propagation.
---

# Error handling conventions

## The core rule: validate at boundaries only

Validate user input, external API responses, and file I/O at the point
they enter the system. Trust internal code and framework guarantees.

```python
# Good — boundary validation
def parse_user_query(raw: str) -> Query:
    if not raw.strip():
        raise ValueError("Query must not be empty")
    return Query(text=raw.strip())

# Bad — internal paranoia
def build_prompt(query: Query) -> str:
    if query is None:           # Query came from parse_user_query — can't be None
        raise ValueError(...)   # unnecessary
    return f"Answer: {query.text}"
```

## Custom exceptions

Define project exceptions in `src/your_project_name/exceptions.py`:

```python
class ProjectError(Exception):
    """Base for all project-specific errors."""

class LLMError(ProjectError):
    """Wraps Anthropic API errors with project context."""

class DataValidationError(ProjectError):
    """Input failed schema validation."""
```

Catch broad `anthropic` exceptions and re-raise as `LLMError` at the
`ClaudeClient` boundary so callers don't need to know the SDK.

## Retry with exponential backoff (API calls only)

```python
import time
import anthropic

def call_with_retry(fn, max_attempts: int = 3) -> str:
    for attempt in range(max_attempts):
        try:
            return fn()
        except anthropic.RateLimitError:
            if attempt == max_attempts - 1:
                raise
            time.sleep(2 ** attempt)   # 1s, 2s, 4s
        except anthropic.APIError as e:
            raise LLMError(f"API error: {e}") from e
```

Only retry on `RateLimitError` and `APIConnectionError`. Never retry
`AuthenticationError` or `InvalidRequestError` — retrying won't help.

## Error propagation

- **Let exceptions bubble** unless you can handle them meaningfully.
- **Wrap, don't swallow:** `raise NewError("context") from original_error`
  preserves the traceback chain.
- **Log at the boundary** where you first catch, not at every re-raise.

```python
# Good
try:
    result = client.chat(prompt)
except anthropic.APIError as e:
    logger.error("LLM call failed: %s", e)
    raise LLMError("Could not complete chat") from e

# Bad — swallowed
try:
    result = client.chat(prompt)
except Exception:
    return ""   # caller has no idea what went wrong
```

## CLI error display (Click)

```python
import click

@cli.command()
def ask(prompt: str):
    try:
        result = client.chat(prompt)
        click.echo(result)
    except LLMError as e:
        raise click.ClickException(str(e))   # prints "Error: ..." and exits 1
```

Never let raw tracebacks reach CLI users.

## What not to do

- No bare `except Exception` or `except:` outside of top-level handlers.
- No `# type: ignore` to paper over a type error — fix the type.
- No `try/except` around code that cannot raise the caught exception.
