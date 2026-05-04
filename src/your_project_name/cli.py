"""Command line interface for your_project_name.

Provides the ``hello`` example plus ``ask`` / ``chat`` commands that talk
to Claude via the project's :mod:`your_project_name.llm` helpers.
"""

from __future__ import annotations

import os
import sys

import click


@click.group()
def cli() -> None:
    """Base command group for your_project_name."""


@cli.command()
@click.argument("name", required=False, default="world")
def hello(name: str) -> None:
    """Print a friendly greeting."""
    click.echo(f"Hello, {name}!")


def _require_api_key() -> None:
    if not os.getenv("ANTHROPIC_API_KEY"):
        raise click.UsageError(
            "ANTHROPIC_API_KEY is not set. "
            "Copy .env.example to .env and fill it in, "
            "or export the variable in your shell."
        )


@cli.command()
@click.argument("prompt", nargs=-1, required=True)
@click.option(
    "--system",
    default="",
    help="System prompt (cached automatically when set).",
)
@click.option(
    "--stream/--no-stream",
    default=True,
    help="Stream the response to stdout (default: stream).",
)
def ask(prompt: tuple[str, ...], system: str, stream: bool) -> None:
    """Send a single prompt to Claude and print the response."""
    _require_api_key()
    from your_project_name.llm import ClaudeClient  # noqa: PLC0415

    client = ClaudeClient(system=system)
    user_message = " ".join(prompt)

    if stream:
        for chunk in client.stream_chat(user_message):
            click.echo(chunk, nl=False)
        click.echo()
    else:
        click.echo(client.chat(user_message))


@cli.command()
@click.option(
    "--system",
    default="You are a concise, helpful assistant.",
    help="System prompt for the conversation.",
)
def chat(system: str) -> None:
    """Start an interactive multi-turn conversation. Type 'exit' to quit."""
    _require_api_key()
    from your_project_name.llm import ConversationClient  # noqa: PLC0415

    conv = ConversationClient(system=system)
    click.echo("Chat started. Type 'exit' or Ctrl-D to quit.\n")

    while True:
        try:
            user_input = click.prompt("you", prompt_suffix="> ")
        except (click.Abort, EOFError):
            click.echo()
            break

        if user_input.strip().lower() in {"exit", "quit"}:
            break

        reply = conv.send(user_input)
        click.echo(f"claude> {reply}\n")


def main() -> None:
    """Entry point for the console script."""
    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
    sys.exit(0)
