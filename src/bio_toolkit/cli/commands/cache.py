from __future__ import annotations

import typer

from bio_toolkit.services.cache import CacheRequest, run_cache

from ..presenters.cache_presenter import render_cache_response
from .common import fail, get_console


def register(app: typer.Typer) -> None:
    @app.command()
    def cache(
        ctx: typer.Context,
        accession: str | None = typer.Argument(
            None,
            help="Optional accession to inspect in detail. Omit it to list cached records.",
        ),
        database: str = typer.Option(
            "",
            "--database",
            "-d",
            help="Optional database filter when listing, or exact database for record lookup.",
        ),
        rettype: str = typer.Option(
            "",
            "--rettype",
            "-r",
            help="Optional format filter when listing, or exact format for record lookup.",
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON output."),
        preview_lines: int = typer.Option(
            8,
            "--preview-lines",
            help="Number of lines to preview when showing a specific cached record.",
        ),
    ) -> None:
        console = get_console(ctx)
        try:
            response = run_cache(
                CacheRequest(
                    accession=accession,
                    database=database,
                    rettype=rettype,
                    preview_lines=preview_lines,
                )
            )
        except Exception as exc:
            fail(console, str(exc))
            return

        render_cache_response(console=console, response=response, as_json=as_json)
