from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int


def render_annotation_response(
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
        if exported_path is not None and export_format is not None:
            console.print(
                f"[green]{export_format.upper()} export written to:[/green] {exported_path}"
            )
        return

    source = report["source"]
    summary_lines = [
        f"Source: {source['kind']}",
        f"Label: {source['label']}",
        f"Input format: {report['input_format']}",
        f"Records annotated: {report['record_count']}",
        f"Feature limit: {report['feature_limit']}",
    ]
    console.print(Panel.fit("\n".join(summary_lines), title="Annotation Report"))
    console.print(_annotation_summary_table(report["records"]))

    if exported_path is not None and export_format is not None:
        console.print(f"[green]{export_format.upper()} export written to:[/green] {exported_path}")


def _annotation_summary_table(records: list[dict[str, Any]]) -> Table:
    table = Table(title="Annotation Summary")
    table.add_column("Accession", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Length", justify="right")
    table.add_column("Organism", style="white")
    table.add_column("Genes", style="magenta")
    table.add_column("Features", justify="right")

    for record in records:
        table.add_row(
            str(record["accession"]),
            str(record["molecule_type"]),
            human_int(record["sequence_length"]),
            str(record["organism"])[:28],
            ", ".join(record["gene_names"][:3]) or "-",
            human_int(record["feature_count"]),
        )

    return table
