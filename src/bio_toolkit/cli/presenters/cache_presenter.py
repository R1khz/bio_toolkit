from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_size


def render_cache_response(*, console: Console, response, as_json: bool) -> None:
    report = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    if as_json:
        payload = (
            report["records"]
            if report.get("record") is None
            else report["record"] | {"content_preview": report.get("preview")}
        )
        console.print_json(json.dumps(payload, indent=2))
        return

    if report.get("record") is None:
        records = report.get("records", [])
        if not records:
            console.print(Panel.fit("Cache is empty.", title="Cache"))
            return

        table = Table(title="Cached Records")
        table.add_column("Accession", style="cyan", no_wrap=True)
        table.add_column("Database", style="green")
        table.add_column("Format", style="magenta")
        table.add_column("Fetched At", style="white")
        table.add_column("Size", justify="right")
        table.add_column("Path", style="white")

        for item in records:
            table.add_row(
                item["accession"],
                item["database"],
                item["rettype"],
                item["fetched_at"],
                human_size(item["file_size"]),
                item["content_path"],
            )

        console.print(table)
        console.print(f"{len(records)} cached record(s).")
        return

    record = report["record"]
    summary = Table(title="Cached Record")
    summary.add_column("Field", style="cyan")
    summary.add_column("Value", style="white")
    summary.add_row("Accession", record["accession"])
    summary.add_row("Database", record["database"])
    summary.add_row("Format", record["rettype"])
    summary.add_row("Fetched At", record["fetched_at"])
    summary.add_row("Size", human_size(record["file_size"]))
    summary.add_row("Path", record["content_path"])
    console.print(summary)

    preview = report.get("preview") or ""
    if preview:
        console.print(Panel(preview, title="Preview", expand=False))
