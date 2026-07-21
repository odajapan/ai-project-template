"""Pydantic schemas for structured Claude API I/O.

Use ``ToolDefinition`` to declare tools for ``ClaudeClient.chat_with_tools``.
Subclass ``StructuredResponse`` to parse Claude's text output into typed objects.

Example — tool definition::

    from your_project_name.schemas import ToolDefinition

    weather_tool = ToolDefinition(
        name="get_weather",
        description="Return current weather for a city.",
        input_schema={
            "type": "object",
            "properties": {
                "city": {"type": "string", "description": "City name"},
            },
            "required": ["city"],
        },
    )
    text, calls = client.chat_with_tools("Weather in Tokyo?", tools=[weather_tool])

Example — structured response::

    from your_project_name.schemas import StructuredResponse

    class DataSummary(StructuredResponse):
        title: str
        key_points: list[str]
        confidence: float

    summary = DataSummary.from_text(client.chat("Summarise the dataset as JSON."))
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ToolDefinition(BaseModel):
    """Describes a tool that Claude can invoke during ``chat_with_tools``."""

    name: str
    description: str
    input_schema: dict[str, Any]

    def to_tool(self) -> dict[str, Any]:
        """Convert to the dict format expected by the Anthropic SDK."""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": self.input_schema,
        }


class StructuredResponse(BaseModel):
    """Base class for parsing Claude's JSON text output into a typed model.

    Claude must be prompted to return valid JSON matching the subclass fields.
    """

    @classmethod
    def from_text(cls, text: str) -> StructuredResponse:
        """Parse *text* (a JSON string from Claude) into this model."""
        import json

        raw = json.loads(text)
        return cls.model_validate(raw)
