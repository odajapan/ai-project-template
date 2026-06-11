---
name: fastapi-patterns
description: FastAPI conventions for this project — router structure, Pydantic I/O, ClaudeClient injection, streaming LLM responses, and error handling.
---

# FastAPI patterns

## App structure

```
src/your_project_name/
  api/
    __init__.py
    app.py          # create_app() factory
    routers/
      chat.py       # /chat endpoints
      health.py     # /health
    dependencies.py # shared Depends() providers
    schemas.py      # request/response Pydantic models (separate from LLM schemas)
```

Keep FastAPI code in `api/`; keep `llm.py` and `schemas.py` framework-agnostic.

## App factory

```python
# api/app.py
from fastapi import FastAPI
from .routers import chat, health

def create_app() -> FastAPI:
    app = FastAPI(title="your_project_name")
    app.include_router(health.router)
    app.include_router(chat.router, prefix="/chat")
    return app

app = create_app()
```

Run with: `uvicorn your_project_name.api.app:app --reload`

## Injecting ClaudeClient

```python
# api/dependencies.py
from your_project_name.llm import ClaudeClient

def get_client() -> ClaudeClient:
    return ClaudeClient()

# api/routers/chat.py
from fastapi import Depends
from ..dependencies import get_client

@router.post("/")
def chat(req: ChatRequest,                          # sync — ClaudeClient is sync
         client: ClaudeClient = Depends(get_client)) -> ChatResponse:
    text = client.chat(req.message)
    return ChatResponse(reply=text)
```

Note: `@lru_cache` on `get_client()` caches a real instance at import time,
making test isolation via `patch()` unreliable. Always override with
`app.dependency_overrides` in tests (see Testing section below).

## Streaming LLM responses (SSE)

`ClaudeClient.stream_chat()` is a sync generator. Use a **sync** handler
so FastAPI runs it in a thread pool instead of blocking the event loop:

```python
from fastapi.responses import StreamingResponse

@router.post("/stream")
def stream_chat(req: ChatRequest,              # sync — NOT async def
                client: ClaudeClient = Depends(get_client)):
    def generate():
        for chunk in client.stream_chat(req.message):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

Using `async def` with a sync blocking generator stalls the event loop
for the full stream duration, serializing all concurrent SSE clients.

## Request / response schemas

```python
# api/schemas.py  — separate from src/your_project_name/schemas.py
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=4096)
    model: str = Field(default="claude-sonnet-4-6")

class ChatResponse(BaseModel):
    reply: str
    input_tokens: int
    output_tokens: int
```

## Error responses

```python
from fastapi import HTTPException
from your_project_name.exceptions import LLMError

@router.post("/")
async def chat(req: ChatRequest, client: ClaudeClient = Depends(get_client)):
    try:
        text = client.chat(req.message)
    except LLMError as e:
        raise HTTPException(status_code=502, detail=str(e))
    return ChatResponse(reply=text, ...)
```

Return 502 for upstream LLM failures, 422 (auto) for validation errors,
400 for bad user input caught in application logic.

## Testing FastAPI endpoints

Always use `dependency_overrides` — do not `patch()` ClaudeClient directly,
since the override is the FastAPI-idiomatic approach and avoids import-time
caching issues:

```python
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from your_project_name.api.app import create_app
from your_project_name.api.dependencies import get_client

def test_chat_endpoint():
    app = create_app()
    mock_client = MagicMock()
    mock_client.chat.return_value = "hello"
    app.dependency_overrides[get_client] = lambda: mock_client

    client = TestClient(app)
    resp = client.post("/chat/", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json()["reply"] == "hello"

    app.dependency_overrides.clear()  # restore after test
```
