from typer.testing import CliRunner

from bio_toolkit.cli import app


def test_cli_registers_expected_commands() -> None:
    command_names = {item.name for item in app.registered_commands}
    assert command_names == {
        "doctor",
        "start",
        "search",
        "query",
        "fetch",
        "batch",
        "analyze",
        "annotate",
        "compare",
        "transform",
        "blast",
        "cache",
    }


def test_cli_help_keeps_plain_and_pick_flags() -> None:
    runner = CliRunner()
    root_help = runner.invoke(app, ["--help"])
    search_help = runner.invoke(app, ["search", "--help"])
    assert root_help.exit_code == 0
    assert search_help.exit_code == 0
    assert "--plain" in root_help.stdout
    assert "--pick" in search_help.stdout
