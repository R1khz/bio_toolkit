from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int


def render_search_response(
    *,
    console: Console,
    response,
    as_json: bool,
    pick: bool = False,
) -> None:
    if as_json:
        payload = [
            item.model_dump() if hasattr(item, "model_dump") else vars(item)
            for item in response.results
        ]
        console.print_json(json.dumps(payload, indent=2))
        return

    if not response.results:
        console.print(Panel.fit("No results found for the given query.", title="Search"))
        return

    table = Table(title=f"Search Results ({response.database_label})")
    table.add_column("Accession", style="cyan", no_wrap=True)
    table.add_column("Organism", style="green")
    table.add_column("Provider", style="magenta")
    table.add_column("Length", justify="right")
    table.add_column("Title", style="white")

    for item in response.results:
        table.add_row(
            item.accession,
            item.organism or "-",
            response.provider,
            human_int(item.length),
            item.title,
        )

    console.print(table)
    console.print(f"{response.result_count} result(s) returned.")
    if pick:
        console.print("[cyan]Interactive picker enabled.[/cyan]")
