from click.testing import CliRunner

from your_project_name.cli import cli


def test_cli_hello_default() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["hello"])

    assert result.exit_code == 0
    assert "Hello, world!" in result.output


def test_cli_hello_name() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["hello", "Alice"])

    assert result.exit_code == 0
    assert "Hello, Alice!" in result.output
