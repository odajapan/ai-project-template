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
from functools import lru_cache
from your_project_name.llm import ClaudeClient

@lru_cache
def get_client() -> ClaudeClient:
    return ClaudeClient()

# api/routers/chat.py
from fastapi import Depends
from ..dependencies import get_client

@router.post("/")
async def chat(req: ChatRequest,
               client: ClaudeClient = Depends(get_client)) -> ChatResponse:
    text = client.chat(req.message)
    return ChatResponse(reply=text)
```

## Streaming LLM responses (SSE)

```python
from fastapi.responses import StreamingResponse

@router.post("/stream")
async def stream_chat(req: ChatRequest,
                      client: ClaudeClient = Depends(get_client)):
    def generate():
        for chunk in client.stream_chat(req.message):
            yield f"data: {chunk}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
```

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

```python
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from your_project_name.api.app import create_app

def test_chat_endpoint():
    app = create_app()
    with patch("your_project_name.api.dependencies.ClaudeClient") as mock:
        mock.return_value.chat.return_value = "hello"
        client = TestClient(app)
        resp = client.post("/chat/", json={"message": "hi"})
    assert resp.status_code == 200
    assert resp.json()["reply"] == "hello"
```

Override dependencies in tests with `app.dependency_overrides`:
```python
app.dependency_overrides[get_client] = lambda: mock_client
```
