from __future__ import annotations

import json
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .common import human_int


def render_query_response(*, console: Console, response, as_json: bool) -> None:
    report = response.model_dump() if hasattr(response, "model_dump") else dict(response)
    if as_json:
        console.print_json(json.dumps(report, indent=2))
        return

    provider = str(report.get("provider", "")).lower()

    console.print(_provider_query_summary_panel(report))

    results = report.get("results", [])
    if results:
        console.print(_results_table(results, report))

    entry = report.get("entry")
    top_hit_entry = report.get("top_hit_entry")

    for entry_data, label in [(entry, "Entry"), (top_hit_entry, "Top Hit")]:
        if not isinstance(entry_data, dict):
            continue
        if provider == "uniprot":
            _render_uniprot_entry(console, entry_data, label)
        elif provider == "kegg":
            _render_kegg_entry(console, entry_data, label)
        else:
            console.print(_metadata_table(title=label, payload=entry_data))

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
        _render_kegg_sequence_preview(console, sequence_preview)

    alphafold = report.get("alphafold") or report.get("prediction")
    if isinstance(alphafold, dict):
        console.print(_alphafold_table(alphafold))


# ── UniProt ──────────────────────────────────────────────────────────────────


def _render_uniprot_entry(console: Console, entry: dict[str, Any], label: str) -> None:
    table = Table(title=f"UniProt {label}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    def row(display: str, key: str, *, fmt: str = "plain") -> None:
        val = entry.get(key)
        if val in (None, "", [], {}):
            return
        if fmt == "bool":
            rendered = "Yes" if val else "No"
        elif fmt == "int":
            rendered = human_int(val)
        elif fmt == "list":
            rendered = ", ".join(str(v) for v in val[:20]) if val else "-"
        else:
            rendered = str(val)
        table.add_row(display, rendered)

    row("Accession", "accession")
    row("UniProt ID", "entry_id")
    row("Protein", "protein_name")
    row("Organism", "organism")
    row("Gene(s)", "genes", fmt="list")
    row("Reviewed (Swiss-Prot)", "reviewed", fmt="bool")
    row("Protein existence", "protein_existence")
    row("Sequence length", "sequence_length", fmt="int")
    row("Keywords", "keywords", fmt="list")

    console.print(table)

    functions = entry.get("functions")
    if functions:
        console.print(Panel.fit(str(functions).strip(), title="Function / Activity"))

    subcellular = entry.get("subcellular_locations")
    if subcellular:
        console.print(Panel.fit(str(subcellular).strip(), title="Subcellular Location"))

    domains = entry.get("domains")
    if isinstance(domains, list) and domains:
        console.print(_domains_table(domains))

    cross_refs = entry.get("cross_references")
    if isinstance(cross_refs, dict) and cross_refs:
        console.print(_cross_references_table(cross_refs))

    seq_preview = entry.get("sequence_preview")
    if seq_preview:
        console.print(Panel.fit(str(seq_preview), title="Sequence Preview"))


def _domains_table(domains: list[dict[str, Any]]) -> Table:
    table = Table(title="Domains / Regions")
    table.add_column("Name", style="cyan")
    table.add_column("Type", style="yellow")
    table.add_column("Residues", justify="right", style="white")
    for d in domains[:20]:
        name = str(d.get("name", "-"))
        evidence = str(d.get("evidence", "-"))
        start = d.get("start_aa")
        end = d.get("end_aa")
        residues = f"{start}–{end}" if start and end else "-"
        table.add_row(name, evidence, residues)
    return table


def _cross_references_table(cross_refs: dict[str, Any]) -> Table:
    priority = ["PDB", "RefSeq", "Ensembl", "GeneID", "OMIM", "ChEMBL", "STRING", "IntAct"]
    table = Table(title="Cross-references")
    table.add_column("Database", style="cyan", no_wrap=True)
    table.add_column("IDs", style="white")
    shown = set()
    for db in priority:
        val = cross_refs.get(db)
        if val:
            ids = val if isinstance(val, list) else [val]
            table.add_row(db, ", ".join(str(i) for i in ids[:6]))
            shown.add(db)
    for db, val in cross_refs.items():
        if db not in shown and val:
            ids = val if isinstance(val, list) else [val]
            table.add_row(db, ", ".join(str(i) for i in ids[:6]))
    return table


# ── KEGG ─────────────────────────────────────────────────────────────────────


def _render_kegg_entry(console: Console, entry: dict[str, Any], label: str) -> None:
    table = Table(title=f"KEGG {label}", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    def row(display: str, key: str) -> None:
        val = entry.get(key)
        if val in (None, "", [], {}):
            return
        table.add_row(display, str(val))

    row("Accession", "accession")
    row("Entry", "entry")
    row("Name", "name")
    row("Definition", "definition")
    row("Organism", "organism")
    row("Genomic position", "position")

    aa_len = entry.get("aa_sequence_length")
    nt_len = entry.get("nt_sequence_length")
    if aa_len:
        table.add_row("AA sequence length", human_int(aa_len))
    if nt_len:
        table.add_row("NT sequence length", human_int(nt_len))

    console.print(table)

    pathways = entry.get("pathways")
    if isinstance(pathways, list) and pathways:
        console.print(_kegg_named_table("Pathways", pathways))

    diseases = entry.get("diseases")
    if isinstance(diseases, list) and diseases:
        console.print(_kegg_named_table("Associated Diseases", diseases))

    orthology = entry.get("orthology")
    if isinstance(orthology, list) and orthology:
        console.print(_kegg_named_table("Orthology (KO)", orthology))

    db_links = entry.get("database_links")
    if isinstance(db_links, dict) and db_links:
        console.print(_kegg_db_links_table(db_links))

    aa_preview = entry.get("aa_sequence_preview")
    if aa_preview:
        console.print(Panel.fit(str(aa_preview), title="AA Sequence Preview"))


def _kegg_named_table(title: str, items: list[dict[str, Any]]) -> Table:
    table = Table(title=title)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")
    for item in items[:20]:
        table.add_row(str(item.get("id", "-")), str(item.get("text", "-")))
    return table


def _kegg_db_links_table(db_links: dict[str, Any]) -> Table:
    table = Table(title="Database Links")
    table.add_column("Database", style="cyan", no_wrap=True)
    table.add_column("IDs", style="white")
    for db, ids in list(db_links.items())[:15]:
        if isinstance(ids, list):
            rendered = ", ".join(str(i) for i in ids[:6])
        else:
            rendered = str(ids)
        table.add_row(str(db), rendered)
    return table


def _render_kegg_sequence_preview(console: Console, preview: dict[str, Any]) -> None:
    table = Table(title="Sequence Info")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="white")
    if preview.get("database"):
        table.add_row("Database", str(preview["database"]))
    if preview.get("length"):
        table.add_row("Length", human_int(preview["length"]))
    if preview.get("preview"):
        table.add_row("Preview", str(preview["preview"]))
    console.print(table)


# ── AlphaFold ────────────────────────────────────────────────────────────────


def _alphafold_table(prediction: dict[str, Any]) -> Table:
    table = Table(title="AlphaFold Prediction", show_header=True)
    table.add_column("Field", style="cyan", no_wrap=True)
    table.add_column("Value", style="white")

    def row(label: str, key: str, *, fmt: str = "plain") -> None:
        val = prediction.get(key)
        if val is None:
            return
        if fmt == "bool":
            rendered = "Yes" if val else "No"
        elif fmt == "int":
            rendered = human_int(val)
        elif fmt == "pct":
            rendered = f"{val}%"
        else:
            rendered = str(val)
        table.add_row(label, rendered)

    row("Accession", "accession")
    row("Gene", "gene")
    row("UniProt ID", "uniprot_id")
    row("Protein", "description")
    row("Organism", "organism")
    row("Entry ID", "entry_id")
    row("Sequence length", "sequence_length", fmt="int")
    row("Avg pLDDT", "avg_plddt")
    row("pLDDT very high (>90)", "plddt_very_high_pct", fmt="pct")
    row("pLDDT confident (70–90)", "plddt_confident_pct", fmt="pct")
    row("pLDDT low (50–70)", "plddt_low_pct", fmt="pct")
    row("pLDDT very low (<50)", "plddt_very_low_pct", fmt="pct")
    row("Reviewed (Swiss-Prot)", "is_reviewed", fmt="bool")
    row("Model version", "latest_version")
    row("Created", "created_date")
    row("Tool", "tool")
    row("View entry", "entry_url")
    row("Download PDB", "pdb_url")
    row("Download CIF", "cif_url")

    return table


# ── NCBI / generic ───────────────────────────────────────────────────────────


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
        if value in (None, "", [], {}):
            continue
        if isinstance(value, list):
            rendered = ", ".join(str(item) for item in value[:8]) or "-"
        elif isinstance(value, dict):
            rendered = json.dumps(value, indent=2)
        else:
            rendered = str(value)
        table.add_row(str(key), rendered)
    return table
