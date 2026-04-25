from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from bio_toolkit.providers.ncbi.client import default_fetch_path

from .common import preview_text, write_text_export


def render_fetch_response(
    *,
    console: Console,
    settings,
    response,
    output: Path | None,
    stdout: bool,
    preview_lines: int,
) -> Path | None:
    if stdout:
        console.print(response.record.content)
        return None

    destination = write_text_export(
        output=output,
        default_output=default_fetch_path(
            settings.output_dir,
            response.accession,
            response.record.rettype,
        ),
        content=response.record.content,
    )

    summary = Table(title="Fetched Record")
    summary.add_column("Field", style="cyan")
    summary.add_column("Value", style="white")
    summary.add_row("Accession", response.record.accession)
    summary.add_row("Database", response.record.database)
    summary.add_row("Format", response.record.rettype)
    summary.add_row("Retrieved From", response.record.source)
    summary.add_row("Output", str(destination))
    if response.cache_path is not None:
        summary.add_row("Cache Path", response.cache_path)
    console.print(summary)

    preview = preview_text(response.record.content, preview_lines)
    if preview:
        console.print(Panel(preview, title="Preview", expand=False))

    return destination
