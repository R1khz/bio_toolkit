from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from bio_toolkit.cli import app


def test_query_command_builds_query_request() -> None:
    runner = CliRunner()

    with patch("bio_toolkit.cli.commands.query.run_query") as run_query:
        run_query.return_value = SimpleNamespace(
            provider="uniprot",
            kind="entry",
            query="P69905",
            result_count=1,
            model_dump=lambda: {"provider": "uniprot", "kind": "entry", "query": "P69905"},
        )
        result = runner.invoke(
            app,
            [
                "query",
                "P69905",
                "--provider",
                "uniprot",
                "--database",
                "auto",
                "--organism",
                "Homo sapiens",
                "--limit",
                "3",
                "--rettype",
                "gb",
            ],
        )

    assert result.exit_code == 0
    request = run_query.call_args.kwargs["request"]
    assert request.query == "P69905"
    assert request.provider == "uniprot"
    assert request.database == "auto"
    assert request.organism == "Homo sapiens"
    assert request.limit == 3
    assert request.rettype == "gb"

