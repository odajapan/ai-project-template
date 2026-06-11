---
name: api-design
description: REST API design decisions — resource naming, HTTP semantics, error schema, pagination, and versioning.
---

# API design conventions

## Resource naming

- **Plural nouns** for collections: `/chats`, `/documents`, `/tools`
- **Kebab-case** for multi-word: `/chat-sessions`, not `/chatSessions`
- No verbs in paths — use HTTP methods for actions:
  ```
  POST   /chats              create a new chat
  GET    /chats/{id}         fetch one
  DELETE /chats/{id}         delete
  POST   /chats/{id}/messages  append a message (sub-resource action)
  ```

## HTTP method semantics

| Method | Idempotent | Use for |
|---|---|---|
| GET | Yes | Fetch, no side effects |
| POST | No | Create, trigger action |
| PUT | Yes | Full replace |
| PATCH | No | Partial update |
| DELETE | Yes | Remove |

## Consistent error schema

All errors return the same shape so clients can handle them generically:

```json
{
  "error": {
    "code": "llm_unavailable",
    "message": "The upstream LLM API is currently unavailable.",
    "detail": "anthropic.APIConnectionError: timeout after 30s"
  }
}
```

```python
# api/schemas.py
class APIError(BaseModel):
    code: str
    message: str
    detail: str | None = None

class ErrorResponse(BaseModel):
    error: APIError
```

| Status | When |
|---|---|
| 400 | Bad input caught in app logic (not validation — that's 422) |
| 401 | Missing or invalid auth |
| 404 | Resource not found |
| 422 | Request body fails Pydantic validation (FastAPI auto) |
| 429 | Rate limit (proxy from upstream LLM) |
| 502 | Upstream LLM error |
| 503 | Service temporarily unavailable |

## Pagination

For list endpoints, use cursor-based pagination (not offset):

```json
{
  "items": [...],
  "next_cursor": "eyJpZCI6MTIzfQ==",
  "has_more": true
}
```

```python
class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None
    has_more: bool
```

Offset pagination breaks under concurrent inserts — prefer cursors for
any list that changes frequently.

## Versioning

Prefix the router with a version:

```python
app.include_router(v1_router, prefix="/v1")
```

**Do not break existing clients** — add fields freely (non-breaking),
but never remove or rename without a version bump. Document deprecated
fields with a `x-deprecated-at` OpenAPI extension.

## Async vs sync handlers

FastAPI runs sync handlers in a thread pool automatically. Use `async def`
only when you `await` something (DB, HTTP client). Mixing sync Claude SDK
calls into `async def` without `run_in_executor` blocks the event loop:

```python
# If ClaudeClient is sync, keep the handler sync
@router.post("/")
def chat(req: ChatRequest, client: ClaudeClient = Depends(get_client)):
    return ChatResponse(reply=client.chat(req.message))

# Or run sync in executor
import asyncio
@router.post("/async")
async def chat_async(req: ChatRequest, client = Depends(get_client)):
    loop = asyncio.get_event_loop()
    reply = await loop.run_in_executor(None, client.chat, req.message)
    return ChatResponse(reply=reply)
```
