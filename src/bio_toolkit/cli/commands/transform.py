from __future__ import annotations

from pathlib import Path

import typer

from bio_toolkit.config import ensure_runtime_dirs, refresh_settings
from bio_toolkit.domain.sequences import default_transform_path
from bio_toolkit.services.transform.request import TransformRequest
from bio_toolkit.services.transform.service import run_transform

from ..presenters.common import transform_output_label
from ..presenters.transform_presenter import render_transform_response
from .common import fail, get_console

TRANSFORM_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional explicit output file path. Defaults to the configured output directory.",
)


def register(app: typer.Typer) -> None:
    @app.command(help="Transform local or cached sequence records.")
    def transform(
        ctx: typer.Context,
        target: str = typer.Argument(
            ..., help="Local sequence file path or cached accession to transform."
        ),
        operation: str = typer.Option(
            "reverse-complement",
            "--operation",
            "-m",
            help="Transform to run: reverse-complement, translate, or subseq.",
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
            help="Optional cache database when transforming cached accessions.",
        ),
        rettype: str = typer.Option(
            "", "--rettype", "-r", help="Optional cache format when transforming cached accessions."
        ),
        frame: int = typer.Option(
            1, "--frame", help="Translation frame for translate: 1, 2, or 3."
        ),
        to_stop: bool = typer.Option(
            False, "--to-stop", help="Stop translation at the first stop codon."
        ),
        start: int = typer.Option(1, "--start", help="1-based inclusive subsequence start."),
        end: int = typer.Option(
            0, "--end", help="1-based inclusive subsequence end. Use 0 for end-of-sequence."
        ),
        output: Path | None = TRANSFORM_OUTPUT_OPTION,
        stdout: bool = typer.Option(False, "--stdout", help="Print transformed FASTA to stdout."),
        preview_lines: int = typer.Option(
            8,
            "--preview-lines",
            help="Number of leading lines to preview after saving transformed output.",
        ),
    ) -> None:
        console = get_console(ctx)
        try:
            settings = refresh_settings()
            if output is None and not stdout:
                ensure_runtime_dirs(settings)
            response = run_transform(
                TransformRequest(
                    target=target,
                    operation=operation,
                    source=source,
                    input_format=input_format,
                    database=database,
                    rettype=rettype,
                    frame=frame,
                    to_stop=to_stop,
                    start=start,
                    end=end,
                ),
                settings=settings,
            )
        except Exception as exc:
            fail(console, str(exc))
            return

        destination = output or default_transform_path(
            settings.output_dir,
            transform_output_label(response.source.model_dump()),
            response.operation,
        )
        render_transform_response(
            console=console,
            response=response,
            destination=destination,
            stdout=stdout,
            preview_lines=preview_lines,
        )
