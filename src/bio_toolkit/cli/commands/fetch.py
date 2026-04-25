from __future__ import annotations

from pathlib import Path

import typer

from bio_toolkit.config import ensure_runtime_dirs, refresh_settings
from bio_toolkit.providers.ncbi.client import SUPPORTED_DATABASES
from bio_toolkit.services.fetch.request import FetchRequest
from bio_toolkit.services.fetch.service import run_fetch

from ..presenters.fetch_presenter import render_fetch_response
from .common import fail, get_console

FETCH_OUTPUT_OPTION = typer.Option(
    None,
    "--output",
    "-O",
    help="Optional explicit output file path. Defaults to the configured output directory.",
)


def register(app: typer.Typer) -> None:
    @app.command()
    def fetch(
        ctx: typer.Context,
        accession: str = typer.Argument(
            ...,
            help="NCBI accession or accession.version to retrieve.",
        ),
        database: str = typer.Option(
            "nucleotide",
            "--database",
            "-d",
            help=f"NCBI database to fetch from ({', '.join(sorted(SUPPORTED_DATABASES))}).",
        ),
        rettype: str = typer.Option(
            "fasta",
            "--rettype",
            "-r",
            help="Remote record format to fetch: fasta, gb, or genbank.",
        ),
        output: Path | None = FETCH_OUTPUT_OPTION,
        stdout: bool = typer.Option(False, "--stdout", help="Print the fetched record to stdout."),
        preview_lines: int = typer.Option(
            8,
            "--preview-lines",
            help="Number of leading lines to preview after saving the record.",
        ),
        use_cache: bool = typer.Option(
            True,
            "--use-cache/--no-use-cache",
            help="Reuse a matching cached record before making a new NCBI request.",
        ),
        refresh: bool = typer.Option(
            False,
            "--refresh",
            help="Bypass any cached copy and force a fresh NCBI request.",
        ),
        save_cache: bool = typer.Option(
            True,
            "--cache/--no-cache",
            help="Save fetched records into the local cache.",
        ),
    ) -> None:
        """Fetch a sequence record by accession."""
        console = get_console(ctx)

        try:
            settings = refresh_settings()
            ensure_runtime_dirs(settings)
            response = run_fetch(
                request=FetchRequest(
                    accession=accession,
                    database=database,
                    rettype=rettype,
                    use_cache=use_cache,
                    refresh=refresh,
                    save_cache=save_cache,
                ),
                settings=settings,
            )
        except Exception as exc:
            fail(console, str(exc))
            return

        render_fetch_response(
            console=console,
            settings=settings,
            response=response,
            output=output,
            stdout=stdout,
            preview_lines=preview_lines,
        )
