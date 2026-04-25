from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from bio_toolkit.cli import app


def test_fetch_command_builds_fetch_request() -> None:
    runner = CliRunner()

    with patch("bio_toolkit.cli.commands.fetch.ensure_runtime_dirs"):
        with patch("bio_toolkit.cli.commands.fetch.run_fetch") as run_fetch:
            run_fetch.return_value = SimpleNamespace(
                accession="NM_000546",
                cache_hit=False,
                cache_path=None,
                record=SimpleNamespace(
                    accession="NM_000546",
                    database="nucleotide",
                    rettype="fasta",
                    source="ncbi",
                    content=">NM_000546\nATGC\n",
                ),
            )
            result = runner.invoke(
                app,
                [
                    "fetch",
                    "NM_000546",
                    "--database",
                    "nucleotide",
                    "--rettype",
                    "fasta",
                    "--no-use-cache",
                    "--refresh",
                    "--no-cache",
                    "--stdout",
                ],
            )

    assert result.exit_code == 0
    request = run_fetch.call_args.kwargs["request"]
    assert request.accession == "NM_000546"
    assert request.database == "nucleotide"
    assert request.rettype == "fasta"
    assert request.use_cache is False
    assert request.refresh is True
    assert request.save_cache is False

