from __future__ import annotations

from pathlib import Path

import typer

from bio_toolkit.config import ensure_runtime_dirs, refresh_settings
from bio_toolkit.exporters import render_batch_export
from bio_toolkit.services.batch import BatchRequest, run_batch

from ..presenters.batch_presenter import render_batch_response
from ..presenters.common import resolve_report_export_format, write_text_export
from .common import fail, get_console

BATCH_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional JSON or CSV output path for the batch report.",
)

BATCH_TARGETS_ARGUMENT = typer.Argument(
    ...,
    help="Path to a newline-delimited file of accessions or local file paths.",
)


def register(app: typer.Typer) -> None:
    @app.command()
    def batch(
        ctx: typer.Context,
        targets_file: Path = BATCH_TARGETS_ARGUMENT,
        mode: str = typer.Option(
            "analyze",
            "--mode",
            "-m",
            help="Batch operation to run: analyze or fetch.",
        ),
        input_kind: str = typer.Option(
            "auto",
            "--input-kind",
            "-k",
            help="Interpret input lines as auto, accessions, or files.",
        ),
        database: str = typer.Option("nucleotide", "--database", "-d", help="NCBI database."),
        rettype: str = typer.Option(
            "fasta",
            "--rettype",
            "-r",
            help="Record format for accession items: fasta, gb, or genbank.",
        ),
        input_format: str = typer.Option(
            "auto",
            "--input-format",
            "-f",
            help="Input format for local sequence files: auto, fasta, genbank, or gb.",
        ),
        min_orf_aa: int = typer.Option(
            30,
            "--min-orf-aa",
            help="Minimum ORF length in amino acids for nucleotide analysis.",
        ),
        use_cache: bool = typer.Option(
            True,
            "--use-cache/--no-use-cache",
            help="Reuse cached accession records before contacting NCBI.",
        ),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            help="Force fresh NCBI retrieval for accession items.",
        ),
        fail_fast: bool = typer.Option(
            False,
            "--fail-fast",
            help="Stop the batch on the first item that fails.",
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit the full batch report as JSON."),
        output: Path | None = BATCH_OUTPUT_OPTION,
        export_format: str = typer.Option(
            "auto",
            "--export-format",
            help="Export format when using --output: auto, json, or csv.",
        ),
    ) -> None:
        console = get_console(ctx)
        try:
            settings = refresh_settings()
            if mode.strip().lower() == "fetch" or input_kind.strip().lower() != "files":
                ensure_runtime_dirs(settings)
            if output is None and export_format.strip().lower() != "auto":
                fail(console, "Use --output together with --export-format.")
                return

            with console.status("Preparing batch...") as status:
                response = run_batch(
                    BatchRequest(
                        targets_file=str(targets_file),
                        mode=mode,
                        input_kind=input_kind,
                        database=database,
                        rettype=rettype,
                        input_format=input_format,
                        min_orf_aa=min_orf_aa,
                        use_cache=use_cache,
                        refresh=refresh,
                        fail_fast=fail_fast,
                    ),
                    settings=settings,
                    status=status,
                )
        except Exception as exc:
            fail(console, str(exc))
            return

        normalized_export_format = None
        exported_path = None
        if output is not None:
            normalized_export_format = resolve_report_export_format(export_format, output)
            exported_path = write_text_export(
                output=output,
                default_output=output,
                content=render_batch_export(response.model_dump(), normalized_export_format),
            )

        render_batch_response(
            console=console,
            response=response,
            as_json=as_json,
            exported_path=exported_path,
            export_format=normalized_export_format,
        )
