"""Single-turn chat with a cached system prompt.

Run::

    python examples/simple_chat.py
"""

from __future__ import annotations

from dotenv import load_dotenv

from your_project_name.llm import ClaudeClient

load_dotenv()


def main() -> None:
    client = ClaudeClient(
        system=(
            "You are a concise data analyst. "
            "Answer in one sentence unless asked otherwise."
        ),
    )

    text, usage = client.chat_with_tracking(
        "What's a good first metric to look at when exploring a new dataset?"
    )

    print("Response:")
    print(f"  {text}\n")
    print("Token usage:")
    for key, value in usage.items():
        print(f"  {key}: {value}")


if __name__ == "__main__":
    main()
