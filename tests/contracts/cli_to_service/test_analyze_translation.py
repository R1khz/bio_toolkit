from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from typer.testing import CliRunner

from bio_toolkit.cli import app


def test_analyze_command_builds_analyze_request() -> None:
    runner = CliRunner()

    with TemporaryDirectory() as tmpdir:
        fasta = Path(tmpdir) / "seq.fasta"
        fasta.write_text(">seq1\nATGGCCAAATGA\n", encoding="utf-8")

        with patch("bio_toolkit.cli.commands.analyze.run_analysis") as run_analysis:
            run_analysis.return_value = SimpleNamespace(
                source=SimpleNamespace(kind="file", label=str(fasta.resolve())),
                input_format="fasta",
                record_count=1,
                records=[],
                model_dump=lambda: {
                    "source": {"kind": "file", "label": str(fasta.resolve())},
                    "input_format": "fasta",
                    "record_count": 1,
                    "records": [],
                },
            )
            result = runner.invoke(
                app,
                [
                    "analyze",
                    str(fasta),
                    "--source",
                    "file",
                    "--input-format",
                    "auto",
                    "--database",
                    "nucleotide",
                    "--rettype",
                    "fasta",
                    "--min-orf-aa",
                    "2",
                    "--motif",
                    "GAATTC",
                ],
            )

    assert result.exit_code == 0
    request = run_analysis.call_args.kwargs["request"]
    assert request.target == str(fasta)
    assert request.source == "file"
    assert request.input_format == "auto"
    assert request.database == "nucleotide"
    assert request.rettype == "fasta"
    assert request.min_orf_aa == 2
    assert request.motifs == ["GAATTC"]
