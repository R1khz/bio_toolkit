from typer.main import get_command
from typer.testing import CliRunner

from bio_toolkit.cli import app


def test_command_surface_contains_expected_commands() -> None:
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


def test_core_command_help_surfaces_options() -> None:
    runner = CliRunner()
    assert runner.invoke(app, ["search", "--help"]).exit_code == 0
    assert runner.invoke(app, ["query", "--help"]).exit_code == 0
    assert runner.invoke(app, ["fetch", "--help"]).exit_code == 0
    assert runner.invoke(app, ["analyze", "--help"]).exit_code == 0
