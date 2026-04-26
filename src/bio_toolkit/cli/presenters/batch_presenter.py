from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int


def render_batch_response(
    *,
    console: Console,
    response,
    as_json: bool,
    exported_path,
    export_format: str | None,
) -> None:
    report = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    summary_lines = [
        f"Mode: {report['mode']}",
        f"Input kind: {report['input_kind']}",
        f"Targets file: {report['targets_file']}",
        f"Items processed: {report['total_items']}",
        f"Succeeded: {report['succeeded']}",
        f"Failed: {report['failed']}",
    ]
    console.print(Panel.fit("\n".join(summary_lines), title="Batch Summary"))

    table = Table(title="Batch Results")
    table.add_column("Item", style="cyan")
    table.add_column("Kind", style="green")
    table.add_column("Status", style="white")
    table.add_column("Result", style="magenta")
    table.add_column("Notes", style="white")

    for item in report["results"]:
        result_label = item.get("accession") or item.get("label") or "-"
        if item["operation"] == "analyze" and item["status"] == "ok":
            notes = (
                f"{human_int(item.get('record_count'))} record(s), "
                f"{', '.join(item.get('molecule_types', [])) or '-'}"
            )
        elif item["operation"] == "fetch" and item["status"] == "ok":
            notes = item.get("saved_to", "-")
        else:
            notes = item.get("error", "-")

        table.add_row(
            str(item["item"])[:32],
            item.get("source_kind", "-"),
            item["status"],
            str(result_label)[:40],
            str(notes)[:56],
        )

    console.print(table)
    if exported_path is not None and export_format is not None:
        console.print(
            f"[green]{export_format.upper()} batch report written to:[/green] {exported_path}"
        )
