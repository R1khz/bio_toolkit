from __future__ import annotations

from pathlib import Path

import typer

from bio_toolkit.config import refresh_settings
from bio_toolkit.domain.annotations import default_annotation_export_path
from bio_toolkit.exporters import normalize_export_format, render_annotation_export
from bio_toolkit.services.annotate.request import AnnotateRequest
from bio_toolkit.services.annotate.service import run_annotation

from ..presenters.annotation_presenter import render_annotation_response
from ..presenters.common import annotation_output_label, write_text_export
from .common import fail, get_console

ANNOTATE_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional export file path for annotation output.",
)


def register(app: typer.Typer) -> None:
    @app.command(help="Inspect record metadata and selected features.")
    def annotate(
        ctx: typer.Context,
        target: str = typer.Argument(
            ...,
            help="Local sequence file path or cached accession to annotate.",
        ),
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
            "",
            "--database",
            "-d",
            help="Optional cache database when annotating cached accessions.",
        ),
        rettype: str = typer.Option(
            "", "--rettype", "-r", help="Optional cache format when annotating cached accessions."
        ),
        feature_limit: int = typer.Option(
            10,
            "--feature-limit",
            help="Maximum number of feature summaries to include per record.",
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON to stdout."),
        output: Path | None = ANNOTATE_OUTPUT_OPTION,
        export_format: str = typer.Option(
            "json",
            "--export-format",
            help="Export format when using --output: json, csv, markdown, or html.",
        ),
    ) -> None:
        console = get_console(ctx)
        try:
            settings = refresh_settings()
            response = run_annotation(
                AnnotateRequest(
                    target=target,
                    source=source,
                    input_format=input_format,
                    database=database,
                    rettype=rettype,
                    feature_limit=feature_limit,
                ),
                settings=settings,
            )
            normalized_export_format = normalize_export_format(export_format)
        except Exception as exc:
            fail(console, str(exc))
            return

        exported_path = None
        if output is not None:
            exported_path = write_text_export(
                output=output,
                default_output=default_annotation_export_path(
                    settings.output_dir,
                    annotation_output_label(response.source.model_dump()),
                    normalized_export_format,
                ),
                content=render_annotation_export(response.model_dump(), normalized_export_format),
            )

        render_annotation_response(
            console=console,
            response=response,
            as_json=as_json,
            exported_path=exported_path,
            export_format=normalized_export_format if exported_path is not None else None,
        )
