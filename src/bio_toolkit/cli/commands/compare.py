from __future__ import annotations

import json
from pathlib import Path

import typer

from bio_toolkit.config import refresh_settings
from bio_toolkit.services.compare.request import CompareRequest
from bio_toolkit.services.compare.service import run_compare

from ..completions import complete_cached_accession
from ..presenters.common import write_text_export
from ..presenters.compare_presenter import render_compare_response
from .common import fail, get_console

COMPARE_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional JSON output path for the comparison report.",
)

COMPARE_TARGETS_ARGUMENT = typer.Argument(
    ...,
    help="Two or more local file paths or cached accessions to compare.",
    autocompletion=complete_cached_accession,
)


def register(app: typer.Typer) -> None:
    @app.command(help="Compare two or more local or cached records.")
    def compare(
        ctx: typer.Context,
        targets: list[str] = COMPARE_TARGETS_ARGUMENT,
        source: str = typer.Option(
            "auto", "--source", "-s", help="Input source: auto, file, or cache."
        ),
        input_format: str = typer.Option(
            "auto",
            "--input-format",
            "-f",
            help="Input format for local or cached content: auto, fasta, genbank, or gb.",
        ),
        database: str = typer.Option(
            "", "--database", "-d", help="Optional cache database when comparing cached accessions."
        ),
        rettype: str = typer.Option(
            "", "--rettype", "-r", help="Optional cache format when comparing cached accessions."
        ),
        min_orf_aa: int = typer.Option(
            30, "--min-orf-aa", help="Minimum ORF length in amino acids for nucleotide comparison."
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
        output: Path | None = COMPARE_OUTPUT_OPTION,
    ) -> None:
        console = get_console(ctx)
        if len(targets) < 2:
            fail(console, "Compare requires at least two targets.")

        try:
            response = run_compare(
                CompareRequest(
                    targets=targets,
                    source=source,
                    input_format=input_format,
                    database=database,
                    rettype=rettype,
                    min_orf_aa=min_orf_aa,
                ),
                settings=refresh_settings(),
            )
        except Exception as exc:
            fail(console, str(exc))
            return

        if output is not None:
            write_text_export(
                output=output,
                default_output=output,
                content=json.dumps(response.model_dump(), indent=2),
            )

        render_compare_response(console=console, response=response, as_json=as_json, output=output)
