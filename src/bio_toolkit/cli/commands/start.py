from __future__ import annotations

import typer

from bio_toolkit.cli.interactive.picker import (
    InteractivePickerCancelled,
    InteractivePickerError,
    prompt_guided_search,
)
from bio_toolkit.config import refresh_settings
from bio_toolkit.services.analyze.response import AnalyzeResponse
from bio_toolkit.services.search.response import SearchResponse
from bio_toolkit.services.start import StartRequest, run_start

from ..interactive.search_flow import run_interactive_search_flow
from ..presenters.analysis_presenter import render_analysis_response
from ..presenters.query_presenter import render_query_response
from ..presenters.search_presenter import render_search_response
from .common import fail, format_cli_error, get_console


def register(app: typer.Typer) -> None:
    @app.command(help="Guided search and action picker.")
    def start(ctx: typer.Context) -> None:
        console = get_console(ctx)
        try:
            search_input = prompt_guided_search()
            settings = refresh_settings()
            response = run_start(
                StartRequest(
                    mode=str(search_input["mode"]),
                    query=str(search_input["query"]),
                    provider=str(search_input["provider"]),
                    database=str(search_input["database"]),
                    organism=str(search_input["organism"]),
                    limit=int(search_input["limit"]),
                ),
                settings=settings,
            )
        except InteractivePickerCancelled:
            console.print("[yellow]Guided search cancelled.[/yellow]")
            return
        except InteractivePickerError as exc:
            fail(console, str(exc))
            return
        except Exception as exc:
            fail(console, format_cli_error(exc))
            return

        if response.kind == "analysis":
            render_analysis_response(
                console=console,
                response=AnalyzeResponse.model_validate(response.payload),
                as_json=False,
                exported_path=None,
                export_format=None,
            )
            return

        if response.kind == "query":
            render_query_response(
                console=console,
                response=response.payload,
                as_json=False,
            )
            return

        search_response = SearchResponse.model_validate(response.payload)
        render_search_response(console=console, response=search_response, as_json=False, pick=False)
        if not search_response.results:
            return

        from types import SimpleNamespace

        interactive_results = [
            SimpleNamespace(
                accession=item.accession,
                title=item.title,
                organism=item.organism or "-",
                source_db=search_response.database_label,
                uid=item.accession,
                length=item.length,
                provider=search_response.provider,
                database=search_response.database_label.split(":", 1)[-1]
                if ":" in search_response.database_label
                else search_response.database_label,
            )
            for item in search_response.results
        ]
        try:
            run_interactive_search_flow(
                console=console,
                settings=settings,
                database=str(search_input["database"]),
                results=interactive_results,
            )
        except Exception as exc:
            fail(console, format_cli_error(exc))
