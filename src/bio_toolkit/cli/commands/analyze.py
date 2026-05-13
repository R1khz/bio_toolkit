from __future__ import annotations

from pathlib import Path

import typer

from bio_toolkit.config import refresh_settings
from bio_toolkit.exporters import render_analysis_export
from bio_toolkit.services.analyze.request import AnalyzeRequest
from bio_toolkit.services.analyze.service import run_analysis

from ..completions import complete_cached_accession
from ..presenters.analysis_presenter import render_analysis_response
from ..presenters.common import resolve_report_export_format, write_text_export
from .common import fail, get_console

ANALYZE_MOTIF_OPTION = typer.Option(
    None,
    "--motif",
    help=(
        "Custom motif to search for during analysis. Repeat for multiple motifs. "
        "Use 're:<pattern>' for regex."
    ),
)
ANALYZE_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional JSON output path for the analysis report.",
)


def register(app: typer.Typer) -> None:
    @app.command()
    def analyze(
        ctx: typer.Context,
        target: str = typer.Argument(
            ...,
            help="Local sequence file path or cached accession, depending on --source.",
            autocompletion=complete_cached_accession,
        ),
        source: str = typer.Option(
            "auto",
            "--source",
            "-s",
            help="Input source: auto, file, or cache.",
        ),
        input_format: str = typer.Option(
            "auto",
            "--input-format",
            "-f",
            help="Input format for local or cached content: auto, fasta, genbank, or gb.",
        ),
        database: str = typer.Option(
            "",
            "--database",
            "-d",
            help="Optional cache database when analyzing a cached accession.",
        ),
        rettype: str = typer.Option(
            "",
            "--rettype",
            "-r",
            help="Optional cache format when analyzing a cached accession.",
        ),
        min_orf_aa: int = typer.Option(
            30,
            "--min-orf-aa",
            help="Minimum ORF length in amino acids for nucleotide analysis.",
        ),
        motif: list[str] | None = ANALYZE_MOTIF_OPTION,
        as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
        output: Path | None = ANALYZE_OUTPUT_OPTION,
        export_format: str = typer.Option(
            "auto",
            "--export-format",
            help="Export format when using --output: auto, json, or csv.",
        ),
    ) -> None:
        """Analyze a local file or cached sequence record."""
        console = get_console(ctx)

        try:
            settings = refresh_settings()
            response = run_analysis(
                request=AnalyzeRequest(
                    target=target,
                    source=source,
                    input_format=input_format,
                    database=database,
                    rettype=rettype,
                    min_orf_aa=min_orf_aa,
                    motifs=motif or [],
                ),
                settings=settings,
            )
        except Exception as exc:
            fail(console, str(exc))
            return

        if output is None and export_format.strip().lower() != "auto":
            fail(console, "Use --output together with --export-format.")

        exported_path = None
        normalized_export_format = None
        if output is not None:
            normalized_export_format = resolve_report_export_format(export_format, output)
            exported_path = write_text_export(
                output=output,
                default_output=output,
                content=render_analysis_export(response.model_dump(), normalized_export_format),
            )

        render_analysis_response(
            console=console,
            response=response,
            as_json=as_json,
            exported_path=exported_path,
            export_format=normalized_export_format,
        )
