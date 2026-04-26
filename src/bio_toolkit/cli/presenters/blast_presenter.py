from __future__ import annotations

import json

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int, metric_value


def render_blast_response(
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

    blast_meta = report["blast"]
    query = report["query"]
    source = report["source"]
    summary_lines = [
        f"RID: {blast_meta['rid']}",
        f"Program: {blast_meta['program']}",
        f"BLAST database: {blast_meta['database']}",
        f"Status: {blast_meta['status']}",
        f"Source: {source['kind']}",
        f"Label: {source['label']}",
        f"Input format: {report['input_format']}",
        f"Query records: {query['record_count']}",
        f"Query kind: {query['query_kind']}",
        f"Elapsed: {blast_meta['elapsed_seconds']}s",
        f"Status checks: {blast_meta['poll_count']}",
    ]
    if blast_meta["estimated_time_seconds"]:
        summary_lines.append(f"NCBI estimate: {blast_meta['estimated_time_seconds']}s")
    console.print(Panel.fit("\n".join(summary_lines), title="Remote BLAST"))

    if report["hit_count"] == 0:
        console.print(
            Panel.fit(
                "BLAST completed successfully but returned no hits for this query.",
                title="BLAST Hits",
            )
        )
    else:
        console.print(_blast_hits_table(report["hits"]))

    if exported_path is not None and export_format is not None:
        console.print(f"[green]{export_format.upper()} export written to:[/green] {exported_path}")


def _blast_hits_table(hits: list[dict]) -> Table:
    table = Table(title="BLAST Hits")
    table.add_column("Query", style="cyan", no_wrap=True)
    table.add_column("Subject", style="green", no_wrap=True)
    table.add_column("% ID", justify="right")
    table.add_column("Align", justify="right")
    table.add_column("E-value", justify="right")
    table.add_column("Bit", justify="right")
    table.add_column("QCov", justify="right")
    table.add_column("Query Range", style="white")
    table.add_column("Subject Range", style="white")

    for hit in hits:
        table.add_row(
            str(hit["query_id"])[:20],
            str(hit["subject_id"])[:20],
            f"{float(hit['percent_identity']):.2f}",
            human_int(hit["alignment_length"]),
            str(hit["e_value"]),
            metric_value(hit["bit_score"]),
            metric_value(hit["query_coverage"], suffix="%")
            if hit["query_coverage"] is not None
            else "-",
            f"{hit['query_start']}-{hit['query_end']}",
            f"{hit['subject_start']}-{hit['subject_end']}",
        )

    return table
