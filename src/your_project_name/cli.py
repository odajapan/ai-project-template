"""Command line interface for your_project_name.

This module provides a small example CLI using click. It is intended as a
starting point for projects created from this template.
"""

from __future__ import annotations

import click


@click.group()
def cli() -> None:
    """Base command group for your_project_name."""


@cli.command()
@click.argument("name", required=False, default="world")
def hello(name: str) -> None:
    """Print a friendly greeting.

    This command is meant as a minimal example of how to structure CLI
    commands with click.
    """

    click.echo(f"Hello, {name}!")


def main() -> None:
    """Entry point for the console script.

    This function is wired up in ``pyproject.toml`` under ``[project.scripts]``
    so that ``your_project_name`` can be executed from the command line once
    the project is installed in editable mode.
    """

    cli(standalone_mode=True)


if __name__ == "__main__":
    main()
