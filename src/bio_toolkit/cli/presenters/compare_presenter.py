from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int, metric_value, source_label


def render_compare_response(*, console: Console, response, as_json: bool, output) -> None:
    report = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    comparison = report["comparison"]
    summary_lines = [
        f"Targets compared: {report['target_count']}",
        f"Records compared: {report['record_count']}",
        f"Molecule types: {', '.join(comparison['molecule_types'])}",
        f"Same molecule type: {str(comparison['all_same_molecule_type']).lower()}",
    ]

    console.print(Panel.fit("\n".join(summary_lines), title="Comparison Report"))
    console.print(_compare_records_table(report["records"]))
    highlight_table = _comparison_highlights_table(comparison)
    if highlight_table is not None:
        console.print(highlight_table)

    if output is not None:
        console.print(f"[green]JSON comparison report written to:[/green] {output}")


def _compare_records_table(records: list[dict[str, Any]]) -> Table:
    table = Table(title="Compared Records")
    table.add_column("Source", style="cyan")
    table.add_column("ID", style="white", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Length", justify="right")
    table.add_column("GC / MW", justify="right")
    table.add_column("ORFs / pI", justify="right")

    for record in records:
        stats = record["analysis"]["basic_stats"]
        molecule_type = record["molecule_type"]
        source_info = record.get("source", {})

        if molecule_type == "PROTEIN":
            gc_or_mw = metric_value(stats.get("molecular_weight"), suffix=" Da")
            orf_or_pi = f"pI {metric_value(stats.get('isoelectric_point'))}"
        else:
            gc_or_mw = metric_value(stats.get("gc_content"), suffix="%")
            orf_or_pi = human_int(record["analysis"]["orfs"].get("orfs_found"))

        table.add_row(
            source_label(source_info),
            str(record["sequence_id"])[:24],
            molecule_type,
            human_int(stats.get("length")),
            gc_or_mw,
            orf_or_pi,
        )

    return table


def _comparison_highlights_table(comparison: dict[str, Any]) -> Table | None:
    table = Table(title="Comparison Highlights")
    table.add_column("Metric", style="cyan")
    table.add_column("Min", justify="right")
    table.add_column("Max", justify="right")
    table.add_column("Delta", justify="right")

    rows_added = 0
    length = comparison.get("length")
    if length is not None:
        table.add_row(
            "Length",
            metric_value(length.get("min")),
            metric_value(length.get("max")),
            metric_value(length.get("delta")),
        )
        rows_added += 1

    nucleotide = comparison.get("nucleotide")
    if nucleotide is not None:
        for label, key, suffix in [
            ("GC Content", "gc_content", "%"),
            ("ORF Count", "orf_count", ""),
            ("Restriction Hits", "restriction_site_hits", ""),
            ("CpG Dinucleotides", "cpg_dinucleotides", ""),
        ]:
            metric = nucleotide.get(key)
            if metric is None:
                continue
            table.add_row(
                label,
                metric_value(metric.get("min"), suffix=suffix),
                metric_value(metric.get("max"), suffix=suffix),
                metric_value(metric.get("delta"), suffix=suffix),
            )
            rows_added += 1

    return table if rows_added else None
