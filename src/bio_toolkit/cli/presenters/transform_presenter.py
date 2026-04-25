from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import preview_text, write_text_export


def render_transform_response(
    *,
    console: Console,
    response,
    destination: Path,
    stdout: bool,
    preview_lines: int,
) -> Path | None:
    if stdout:
        console.print(response.fasta_text)
        return None

    write_text_export(output=destination, default_output=destination, content=response.fasta_text)
    summary_lines = [
        f"Operation: {response.operation}",
        f"Source: {response.source.kind}",
        f"Label: {response.source.label}",
        f"Input format: {response.input_format}",
        f"Input records: {response.input_record_count}",
        f"Output records: {response.output_record_count}",
        f"Output format: {response.output_format}",
        f"Output path: {destination}",
    ]
    console.print(Panel.fit("\n".join(summary_lines), title="Transform Output"))
    console.print(_transform_parameters_table(response.parameters))

    preview = preview_text(response.fasta_text, preview_lines)
    if preview:
        console.print(Panel(preview, title="Preview", expand=False))

    return destination


def _transform_parameters_table(parameters: dict) -> Table:
    table = Table(title="Transform Parameters")
    table.add_column("Parameter", style="cyan")
    table.add_column("Value", style="white")

    for key, value in parameters.items():
        if value is None:
            continue
        table.add_row(str(key), str(value))

    return table
