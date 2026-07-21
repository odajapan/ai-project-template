"""Minimal tool-use loop using Anthropic's canonical tool_result flow.

Claude decides whether to call ``get_current_weather``; the script executes
the tool locally and returns the result as a ``tool_result`` block in a
follow-up message, preserving the ``tool_use_id`` linkage.

Run::

    python examples/agent_loop.py
"""

from __future__ import annotations

from typing import Any

from dotenv import load_dotenv

from your_project_name.llm import ClaudeClient
from your_project_name.schemas import ToolDefinition

load_dotenv()

WEATHER_TOOL = ToolDefinition(
    name="get_current_weather",
    description="Return current weather for a city as a short string.",
    input_schema={
        "type": "object",
        "properties": {
            "city": {"type": "string", "description": "City name"},
        },
        "required": ["city"],
    },
)


def get_current_weather(city: str) -> str:
    """Stub implementation — replace with a real API call."""
    fake = {"Tokyo": "sunny, 22°C", "Reykjavik": "snow, -3°C"}
    return fake.get(city, f"unknown weather for {city}")


def run_tool(name: str, args: dict[str, Any]) -> str:
    if name == "get_current_weather":
        return get_current_weather(**args)
    raise ValueError(f"Unknown tool: {name}")


def main() -> None:
    client = ClaudeClient(
        system="You answer weather questions by calling tools when needed.",
    )

    user_message = "What's the weather in Tokyo right now?"

    text, tool_calls, assistant_content = client.chat_with_tools(
        user_message, tools=[WEATHER_TOOL]
    )
    if not tool_calls:
        print(text)
        return

    tool_results = []
    for call in tool_calls:
        result = run_tool(call["name"], call["input"])
        print(f"[tool {call['name']}({call['input']}) -> {result}]")
        tool_results.append({"tool_use_id": call["id"], "content": result})

    final = client.continue_with_tool_results(
        user_message=user_message,
        assistant_content=assistant_content,
        tool_results=tool_results,
        tools=[WEATHER_TOOL],
    )
    print(f"Final answer: {final}")


if __name__ == "__main__":
    main()
