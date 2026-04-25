from __future__ import annotations

import typer

from bio_toolkit.config import refresh_settings
from bio_toolkit.providers import supported_kegg_databases_text, supported_query_providers_text
from bio_toolkit.services.query.request import QueryRequest
from bio_toolkit.services.query.service import run_query

from ..presenters.query_presenter import render_query_response
from .common import fail, get_console


def register(app: typer.Typer) -> None:
    @app.command()
    def query(
        ctx: typer.Context,
        target: str = typer.Argument(
            ...,
            help="Accession, identifier, or free-text term to inspect through provider APIs.",
        ),
        provider: str = typer.Option(
            "auto",
            "--provider",
            "-p",
            help=f"Query provider: {supported_query_providers_text()}.",
        ),
        database: str = typer.Option(
            "auto",
            "--database",
            "-d",
            help=(
                "Database hint. For NCBI use nucleotide or protein. "
                f"For KEGG use one of: {supported_kegg_databases_text()}."
            ),
        ),
        organism: str = typer.Option("", "--organism", "-o", help="Optional organism filter."),
        limit: int = typer.Option(
            5,
            "--limit",
            "-n",
            help="Maximum number of search hits to keep for search-style API queries.",
        ),
        rettype: str = typer.Option(
            "fasta",
            "--rettype",
            "-r",
            help="Preview rettype for exact NCBI matches: fasta, gb, or genbank.",
        ),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of terminal tables."),
    ) -> None:
        """Query provider APIs directly for structured metadata and deeper context."""
        console = get_console(ctx)

        try:
            response = run_query(
                request=QueryRequest(
                    query=target,
                    provider=provider,
                    database=database,
                    organism=organism,
                    limit=limit,
                    rettype=rettype,
                ),
                settings=refresh_settings(),
            )
        except Exception as exc:
            fail(console, str(exc))
            return

        render_query_response(console=console, response=response, as_json=as_json)
