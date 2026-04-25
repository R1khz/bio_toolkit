from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int, metric_value


def render_query_response(*, console: Console, response, as_json: bool) -> None:
    report = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    console.print(_provider_query_summary_panel(report))

    results = report.get("results", [])
    if results:
        console.print(_results_table(results, report))
    entry = report.get("entry")
    if isinstance(entry, dict):
        console.print(_metadata_table(title="Entry", payload=entry))
    top_hit_entry = report.get("top_hit_entry")
    if isinstance(top_hit_entry, dict):
        console.print(_metadata_table(title="Top Hit Entry", payload=top_hit_entry))
    fetch_preview = report.get("fetch_preview")
    if isinstance(fetch_preview, dict):
        console.print(
            Panel.fit(
                fetch_preview.get("preview", ""),
                title=f"Fetch Preview ({fetch_preview.get('rettype', '-')})",
            )
        )
    sequence_preview = report.get("sequence_preview")
    if isinstance(sequence_preview, dict):
        console.print(_metadata_table(title="Sequence Preview", payload=sequence_preview))
    alphafold = report.get("alphafold") or report.get("prediction")
    if isinstance(alphafold, dict):
        console.print(_alphafold_panel(alphafold))


def _provider_query_summary_panel(report: dict[str, Any]) -> Panel:
    lines = [
        f"Provider: {report.get('provider', '-')}",
        f"Query: {report.get('query', '-')}",
        f"Mode: {report.get('kind', '-')}",
    ]
    database = str(report.get("database") or "").strip()
    organism = str(report.get("organism") or "").strip()
    if database:
        lines.append(f"Database: {database}")
    if organism:
        lines.append(f"Organism filter: {organism}")
    if "result_count" in report:
        lines.append(f"Results: {report.get('result_count')}")
    return Panel.fit("\n".join(lines), title="Provider Query")


def _results_table(results: list[dict[str, Any]], report: dict[str, Any]) -> Table:
    table = Table(title=f"Results ({report.get('provider', '-')})")
    table.add_column("Accession", style="cyan", no_wrap=True)
    table.add_column("Organism", style="green")
    table.add_column("Length", justify="right")
    table.add_column("Title", style="white")
    for item in results:
        table.add_row(
            str(item.get("accession", "-")),
            str(item.get("organism", "-")),
            human_int(item.get("length")),
            str(item.get("title", "-")),
        )
    return table


def _metadata_table(*, title: str, payload: dict[str, Any]) -> Table:
    table = Table(title=title)
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    for key, value in payload.items():
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value[:8]) or "-"
        elif isinstance(value, dict):
            rendered = json.dumps(value, indent=2)
        else:
            rendered = str(value)
        table.add_row(str(key), rendered)
    return table


def _alphafold_panel(prediction: dict[str, Any]) -> Panel:
    lines = [
        f"Model ID: {prediction.get('model_id', '-')}",
        f"Entry: {prediction.get('entry_url', '-')}",
    ]
    if prediction.get("avg_plddt") is not None:
        lines.append(f"Average pLDDT: {metric_value(prediction['avg_plddt'])}")
    if prediction.get("sequence_start") is not None and prediction.get("sequence_end") is not None:
        lines.append(
            f"Sequence range: {prediction['sequence_start']} - {prediction['sequence_end']}"
        )
    return Panel.fit("\n".join(lines), title="AlphaFold")
