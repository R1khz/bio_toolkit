from __future__ import annotations

from rich.console import Console
from rich.table import Table


def render_doctor_response(*, console: Console, response) -> None:
    table = Table(title="Runtime Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="white")
    table.add_column("Status", style="green")

    for row in response.rows:
        table.add_row(row.setting, row.value, row.status)

    console.print(table)
    for warning in response.warnings:
        console.print(f"[yellow]{warning}[/yellow]")
