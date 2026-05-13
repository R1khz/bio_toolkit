import re

from typer.main import get_command
from typer.testing import CliRunner

from bio_toolkit.cli import app


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def test_cli_registers_expected_commands() -> None:
    command_names = set(get_command(app).commands)
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
    root_out = _strip_ansi(root_help.stdout)
    search_out = _strip_ansi(search_help.stdout)
    assert "--plain" in root_out
    assert "--pick" in search_out
    assert "--install-completion" in root_out
    assert "--show-completion" in root_out


def test_root_help_includes_descriptions_for_interactive_and_local_commands() -> None:
    runner = CliRunner()
    root_help = runner.invoke(app, ["--help"])
    root_out = _strip_ansi(root_help.stdout)

    assert root_help.exit_code == 0
    assert "Guided search and action picker" in root_out
    assert "Validate local runtime configuration" in root_out
    assert "Inspect local cache contents" in root_out
    assert "Process repeated fetch/analyze work from a list" in root_out
    assert "Run remote BLAST searches from local or cached queries" in root_out
