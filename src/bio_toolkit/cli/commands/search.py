from __future__ import annotations

import typer

from bio_toolkit.config import refresh_settings
from bio_toolkit.providers import supported_kegg_databases_text
from bio_toolkit.services.search.request import SearchRequest
from bio_toolkit.services.search.service import run_search

from ..interactive.search_flow import run_interactive_search_flow
from ..presenters.search_presenter import render_search_response
from .common import fail, format_cli_error, get_console


def register(app: typer.Typer) -> None:
    @app.command()
    def search(
        ctx: typer.Context,
        query: str = typer.Argument(
            ...,
            help="Free-text query, gene name, accession fragment, or term.",
        ),
        database: str = typer.Option(
            "nucleotide",
            "--database",
            "-d",
            help=(
                "Database to search. For NCBI use nucleotide or protein. "
                f"For KEGG use one of: {supported_kegg_databases_text()}."
            ),
        ),
        organism: str = typer.Option("", "--organism", "-o", help="Optional organism filter."),
        provider: str = typer.Option(
            "ncbi",
            "--provider",
            "-p",
            help="Search provider: ncbi, uniprot, kegg, or auto.",
        ),
        limit: int = typer.Option(10, "--limit", "-n", help="Maximum number of results (1-100)."),
        as_json: bool = typer.Option(False, "--json", help="Emit JSON instead of a Rich table."),
        pick: bool = typer.Option(
            False,
            "--pick",
            help="Interactively choose a result and decide what to do next.",
        ),
    ) -> None:
        """Search NCBI, UniProt, or KEGG from the terminal."""
        console = get_console(ctx)

        if as_json and pick:
            fail(console, "--json and --pick cannot be used together.")

        try:
            settings = refresh_settings()
            response = run_search(
                request=SearchRequest(
                    query=query,
                    database=database,
                    organism=organism,
                    provider=provider,
                    limit=limit,
                ),
                settings=settings,
            )
        except Exception as exc:
            fail(console, format_cli_error(exc))
            return

        render_search_response(console=console, response=response, as_json=as_json, pick=pick)

        if pick and response.results:
            from types import SimpleNamespace

            interactive_results = [
                SimpleNamespace(
                    accession=item.accession,
                    title=item.title,
                    organism=item.organism or "-",
                    source_db=response.database_label,
                    uid=item.accession,
                    length=item.length,
                    provider=response.provider,
                    database=database,
                )
                for item in response.results
            ]
            try:
                run_interactive_search_flow(
                    console=console,
                    settings=settings,
                    database=database,
                    results=interactive_results,
                )
            except Exception as exc:
                fail(console, format_cli_error(exc))
