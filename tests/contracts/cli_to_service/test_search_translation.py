from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from bio_toolkit.cli import app


def test_search_command_builds_search_request() -> None:
    runner = CliRunner()

    with patch("bio_toolkit.cli.commands.search.run_search") as run_search:
        run_search.return_value = SimpleNamespace(
            result_count=0,
            results=[],
            provider="ncbi",
            database_label="NCBI:nucleotide",
        )
        result = runner.invoke(
            app,
            ["search", "BRCA1", "--provider", "ncbi", "--database", "nucleotide"],
        )

    assert result.exit_code == 0
    request = run_search.call_args.kwargs["request"]
    assert request.query == "BRCA1"
    assert request.provider == "ncbi"
    assert request.database == "nucleotide"

