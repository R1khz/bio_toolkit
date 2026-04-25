from __future__ import annotations

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bio_toolkit import __version__
from bio_toolkit.config import get_settings


def get_console(ctx: typer.Context | None = None) -> Console:
    settings = get_settings()
    plain = bool(ctx and ctx.obj and ctx.obj.get("plain"))
    return Console(no_color=plain or not settings.color_enabled)


def fail(console: Console, message: str) -> None:
    console.print(f"[red]{message}[/red]")
    raise typer.Exit(code=1)


def register_root_callback(app: typer.Typer) -> None:
    @app.callback(invoke_without_command=True)
    def main(
        ctx: typer.Context,
        plain: bool = typer.Option(
            False,
            "--plain",
            help="Disable color-rich output for limited or log-oriented terminals.",
        ),
    ) -> None:
        ctx.obj = {"plain": plain}
        if ctx.invoked_subcommand is not None:
            return

        console = get_console(ctx)
        console.print(
            Panel.fit(
                (
                    "Bio Toolkit\n"
                    "NCBI search, local cache, and sequence analysis for Linux terminals."
                ),
                title=f"v{__version__}",
            )
        )
        table = Table(title="Command Surface")
        table.add_column("Command", style="cyan")
        table.add_column("Purpose", style="white")
        table.add_row("doctor", "Validate local runtime configuration")
        table.add_row("start", "Guided search and action picker")
        table.add_row("search", "Search NCBI records from the terminal")
        table.add_row("query", "Query provider APIs for deeper metadata")
        table.add_row("fetch", "Download an NCBI record by accession")
        table.add_row("batch", "Process repeated fetch/analyze work from a list")
        table.add_row("analyze", "Analyze a local or cached sequence record")
        table.add_row("annotate", "Inspect record metadata and selected features")
        table.add_row("compare", "Compare two or more local or cached records")
        table.add_row("transform", "Transform local or cached sequence records")
        table.add_row("blast", "Run remote BLAST searches from local or cached queries")
        table.add_row("cache", "Inspect local cache contents")
        console.print(table)
        console.print("Use `python -m bio_toolkit doctor --create-dirs` to validate local setup.")
