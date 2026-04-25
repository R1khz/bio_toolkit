from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int, metric_value


def render_analysis_response(
    *,
    console: Console,
    response,
    as_json: bool,
    exported_path: Path | None,
    export_format: str | None,
) -> None:
    report = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    source = report["source"]
    summary_lines = [
        f"Source: {source['kind']}",
        f"Label: {source['label']}",
        f"Input format: {report['input_format']}",
        f"Records analyzed: {report['record_count']}",
    ]
    if source["kind"] == "cache":
        summary_lines.append(f"Cache database: {source['database']}")
        summary_lines.append(f"Cache format: {source['rettype']}")

    console.print(Panel.fit("\n".join(summary_lines), title="Analysis Report"))
    console.print(_analysis_summary_table(report["records"]))

    if len(report["records"]) == 1:
        _render_single_record_details(console, report["records"][0])

    if exported_path is not None and export_format is not None:
        console.print(f"[green]{export_format.upper()} report written to:[/green] {exported_path}")


def _analysis_summary_table(records: list[dict[str, Any]]) -> Table:
    table = Table(title="Sequence Summary")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Length", justify="right")
    table.add_column("GC / MW", justify="right")
    table.add_column("ORFs / pI", justify="right")
    table.add_column("Description", style="white")

    for record in records:
        stats = record["analysis"]["basic_stats"]
        molecule_type = record["molecule_type"]

        if molecule_type == "PROTEIN":
            gc_or_mw = metric_value(stats.get("molecular_weight"), suffix=" Da")
            orf_or_pi = f"pI {metric_value(stats.get('isoelectric_point'))}"
        else:
            gc_or_mw = metric_value(stats.get("gc_content"), suffix="%")
            orf_or_pi = f"{human_int(record['analysis']['orfs'].get('orfs_found'))} ORFs"

        table.add_row(
            str(record["sequence_id"])[:24],
            molecule_type,
            human_int(stats.get("length")),
            gc_or_mw,
            orf_or_pi,
            str(record["description"])[:44],
        )

    return table


def _render_single_record_details(console: Console, record: dict[str, Any]) -> None:
    console.print(
        Panel(
            record["description"],
            title=f"Record: {record['sequence_id']}",
            expand=False,
        )
    )
    stats = record["analysis"]["basic_stats"]
    console.print(_metric_table(record["molecule_type"], stats))
    warning_panel = _warnings_panel(record["analysis"].get("warnings", []))
    if warning_panel is not None:
        console.print(warning_panel)
    console.print(_composition_table(record["molecule_type"], stats))
    custom_motif_table = _custom_motif_table(record["analysis"].get("custom_motifs", []))
    if custom_motif_table is not None:
        console.print(custom_motif_table)

    if record["molecule_type"] in {"DNA", "RNA"}:
        console.print(_motif_table(record["analysis"]["motifs"]))
        orf_table = _orf_table(record["analysis"]["orfs"])
        if orf_table is not None:
            console.print(orf_table)
        longest_orf_panel = _longest_orf_panel(record["analysis"]["orfs"])
        if longest_orf_panel is not None:
            console.print(longest_orf_panel)
        codon_usage_table = _codon_usage_table(record["analysis"]["orfs"])
        if codon_usage_table is not None:
            console.print(codon_usage_table)
    else:
        domain_table = _protein_domains_table(record["analysis"].get("domains"))
        if domain_table is not None:
            console.print(domain_table)
        alphafold_panel = _alphafold_panel(record["analysis"].get("external", {}).get("alphafold"))
        if alphafold_panel is not None:
            console.print(alphafold_panel)


def _metric_table(molecule_type: str, stats: dict[str, Any]) -> Table:
    table = Table(title="Key Metrics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Molecule Type", molecule_type)
    table.add_row("Length", human_int(stats.get("length")))

    if molecule_type == "PROTEIN":
        for key in [
            "molecular_weight",
            "isoelectric_point",
            "instability_index",
            "gravy",
            "aromaticity",
            "is_stable",
        ]:
            if key in stats:
                suffix = " Da" if key == "molecular_weight" else ""
                table.add_row(key, metric_value(stats[key], suffix=suffix))
    else:
        table.add_row("GC Content", metric_value(stats.get("gc_content"), suffix="%"))
        table.add_row("AT Content", metric_value(stats.get("at_content"), suffix="%"))
        table.add_row("N Count", human_int(stats.get("n_count")))
        table.add_row("Ambiguous Bases", human_int(stats.get("ambiguous_count")))
        table.add_row("Ambiguous Content", metric_value(stats.get("ambiguous_content"), suffix="%"))
        if "melting_temp_tm" in stats:
            table.add_row("Melting Temp (Tm)", metric_value(stats["melting_temp_tm"], suffix=" C"))

    return table


def _warnings_panel(warnings: list[str]) -> Panel | None:
    if not warnings:
        return None
    lines = "\n".join(f"- {warning}" for warning in warnings)
    return Panel.fit(lines, title="Warnings", border_style="yellow")


def _composition_table(molecule_type: str, stats: dict[str, Any]) -> Table:
    table = Table(title="Composition")
    table.add_column("Residue", style="magenta")
    table.add_column("Count", justify="right")

    composition = (
        stats.get("amino_acid_count", {})
        if molecule_type == "PROTEIN"
        else stats.get("base_composition", {})
    )
    for residue, count in composition.items():
        table.add_row(str(residue), human_int(count))

    return table


def _motif_table(motifs: dict[str, Any]) -> Table:
    table = Table(title="Motif Review")
    table.add_column("Feature", style="cyan")
    table.add_column("Value", style="white")
    table.add_row("Restriction Sites Found", human_int(len(motifs.get("restriction_sites", []))))
    table.add_row("Kozak Sequences", human_int(len(motifs.get("kozak_sequences", []))))
    table.add_row("CpG Dinucleotides", human_int(motifs.get("cpg_dinucleotides")))
    table.add_row("Approx. CpG Islands", human_int(motifs.get("cpg_islands_approx")))

    restriction_sites = motifs.get("restriction_sites", [])
    if restriction_sites:
        top_hits = ", ".join(f"{item['enzyme']}({item['count']})" for item in restriction_sites[:5])
        table.add_row("Top Restriction Hits", top_hits)

    return table


def _custom_motif_table(custom_motifs: list[dict[str, Any]]) -> Table | None:
    if not custom_motifs:
        return None

    table = Table(title="Custom Motifs")
    table.add_column("Motif", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Hits", justify="right")
    table.add_column("Positions", style="white")

    for item in custom_motifs:
        table.add_row(
            str(item["label"]),
            str(item["match_type"]),
            human_int(item["count"]),
            _positions_preview(item.get("positions", [])),
        )

    return table


def _orf_table(orfs: dict[str, Any]) -> Table | None:
    all_orfs = orfs.get("all_orfs", [])
    if not all_orfs:
        return None

    table = Table(title=f"Top ORFs (min {orfs.get('min_orf_aa', '-')} aa)")
    table.add_column("Frame", style="cyan")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    table.add_column("AA Length", justify="right")
    table.add_column("Preview", style="white")

    for item in all_orfs[:5]:
        table.add_row(
            str(item["frame"]),
            human_int(item["start_nt"]),
            human_int(item["end_nt"]),
            human_int(item["length_aa"]),
            str(item["protein_preview"]),
        )

    return table


def _longest_orf_panel(orfs: dict[str, Any]) -> Panel | None:
    longest_orf = orfs.get("longest_orf")
    if not longest_orf:
        return None

    protein_sequence = str(longest_orf.get("protein_sequence", ""))
    preview = protein_sequence[:120] + ("..." if len(protein_sequence) > 120 else "")
    lines = [
        f"Frame: {longest_orf.get('frame', '-')}",
        f"Length: {human_int(longest_orf.get('length_aa'))} aa",
        (
            f"Coords: {human_int(longest_orf.get('start_nt'))} - "
            f"{human_int(longest_orf.get('end_nt'))}"
        ),
        f"Translation: {preview or '-'}",
    ]
    return Panel.fit("\n".join(lines), title="Longest ORF Translation")


def _codon_usage_table(orfs: dict[str, Any]) -> Table | None:
    longest_orf = orfs.get("longest_orf")
    if not longest_orf:
        return None

    codon_usage = longest_orf.get("codon_usage") or {}
    if not codon_usage:
        return None

    table = Table(title="Longest ORF Codon Usage")
    table.add_column("Codon", style="cyan")
    table.add_column("Count", justify="right")

    for codon, count in list(codon_usage.items())[:8]:
        table.add_row(str(codon), human_int(count))

    return table


def _positions_preview(positions: list[int]) -> str:
    if not positions:
        return "-"
    preview = ", ".join(str(position) for position in positions[:5])
    if len(positions) > 5:
        return f"{preview}, ..."
    return preview


def _protein_domains_table(domains: dict[str, Any] | None) -> Table | None:
    if not domains or domains.get("skipped"):
        return None

    all_domains = domains.get("all_domains", [])
    if not all_domains:
        return None

    table = Table(title="Protein Domains")
    table.add_column("Name", style="cyan")
    table.add_column("Start", justify="right")
    table.add_column("End", justify="right")
    table.add_column("Source", style="magenta")
    table.add_column("Evidence", style="white")

    for item in all_domains[:8]:
        table.add_row(
            str(item.get("name", "-")),
            human_int(item.get("start_aa")),
            human_int(item.get("end_aa")),
            str(item.get("source", "-")),
            str(item.get("evidence", "-")),
        )

    return table


def _alphafold_panel(prediction: dict[str, Any] | None) -> Panel | None:
    if not prediction:
        return None

    lines = [
        f"Model ID: {prediction.get('model_id', '-')}",
        f"Entry: {prediction.get('entry_url', '-')}",
    ]
    if prediction.get("avg_plddt") is not None:
        lines.append(f"Average pLDDT: {prediction['avg_plddt']}")
    if prediction.get("sequence_start") is not None and prediction.get("sequence_end") is not None:
        lines.append(
            f"Sequence range: {prediction['sequence_start']} - {prediction['sequence_end']}"
        )

    return Panel.fit("\n".join(lines), title="AlphaFold")
