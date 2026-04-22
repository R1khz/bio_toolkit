from __future__ import annotations

import csv
import json
from html import escape
from io import StringIO

SUPPORTED_EXPORT_FORMATS = {"json", "csv", "markdown", "html"}
SUPPORTED_BLAST_EXPORT_FORMATS = {"json", "csv", "tsv"}
SUPPORTED_REPORT_EXPORT_FORMATS = {"json", "csv"}


def normalize_export_format(export_format: str) -> str:
    normalized = export_format.strip().lower()
    if normalized not in SUPPORTED_EXPORT_FORMATS:
        allowed = ", ".join(sorted(SUPPORTED_EXPORT_FORMATS))
        raise ValueError(f"Unsupported export format '{export_format}'. Use one of: {allowed}.")
    return normalized


def render_annotation_export(report: dict, export_format: str) -> str:
    normalized = normalize_export_format(export_format)
    if normalized == "json":
        return json.dumps(report, indent=2)
    if normalized == "csv":
        return _render_annotation_csv(report)
    if normalized == "markdown":
        return _render_annotation_markdown(report)
    return _render_annotation_html(report)


def normalize_blast_export_format(export_format: str) -> str:
    normalized = export_format.strip().lower()
    if normalized not in SUPPORTED_BLAST_EXPORT_FORMATS:
        allowed = ", ".join(sorted(SUPPORTED_BLAST_EXPORT_FORMATS))
        raise ValueError(
            f"Unsupported BLAST export format '{export_format}'. Use one of: {allowed}."
        )
    return normalized


def normalize_report_export_format(export_format: str) -> str:
    normalized = export_format.strip().lower()
    if normalized not in SUPPORTED_REPORT_EXPORT_FORMATS:
        allowed = ", ".join(sorted(SUPPORTED_REPORT_EXPORT_FORMATS))
        raise ValueError(
            f"Unsupported report export format '{export_format}'. Use one of: {allowed}."
        )
    return normalized


def render_analysis_export(report: dict, export_format: str) -> str:
    normalized = normalize_report_export_format(export_format)
    if normalized == "json":
        return json.dumps(report, indent=2)
    return _render_analysis_csv(report)


def render_batch_export(report: dict, export_format: str) -> str:
    normalized = normalize_report_export_format(export_format)
    if normalized == "json":
        return json.dumps(report, indent=2)
    return _render_batch_csv(report)


def render_blast_export(report: dict, export_format: str) -> str:
    normalized = normalize_blast_export_format(export_format)
    if normalized == "json":
        return json.dumps(report, indent=2)
    return _render_blast_delimited(report, delimiter="," if normalized == "csv" else "\t")


def _render_annotation_csv(report: dict) -> str:
    fieldnames = [
        "accession",
        "sequence_id",
        "description",
        "molecule_type",
        "sequence_length",
        "organism",
        "topology",
        "date",
        "source",
        "gene_names",
        "product_names",
        "feature_count",
        "feature_counts",
        "selected_features",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for record in report["records"]:
        writer.writerow(
            {
                "accession": record["accession"],
                "sequence_id": record["sequence_id"],
                "description": record["description"],
                "molecule_type": record["molecule_type"],
                "sequence_length": record["sequence_length"],
                "organism": record["organism"],
                "topology": record["topology"],
                "date": record["date"],
                "source": record["source"],
                "gene_names": "; ".join(record["gene_names"]),
                "product_names": "; ".join(record["product_names"]),
                "feature_count": record["feature_count"],
                "feature_counts": _feature_counts_summary(record["feature_counts"]),
                "selected_features": _selected_features_summary(record["selected_features"]),
            }
        )

    return output.getvalue()


def _render_analysis_csv(report: dict) -> str:
    fieldnames = [
        "source_kind",
        "source_label",
        "input_format",
        "sequence_id",
        "description",
        "molecule_type",
        "length",
        "gc_content",
        "at_content",
        "n_count",
        "ambiguous_count",
        "ambiguous_content",
        "melting_temp_tm",
        "molecular_weight",
        "isoelectric_point",
        "instability_index",
        "gravy",
        "aromaticity",
        "is_stable",
        "orfs_found",
        "longest_orf_frame",
        "longest_orf_aa",
        "longest_orf_translation_preview",
        "top_codons",
        "domains_found",
        "domain_names",
        "alphafold_model_id",
        "alphafold_avg_plddt",
        "restriction_hits",
        "kozak_hits",
        "cpg_dinucleotides",
        "custom_motif_hits",
        "custom_motifs",
        "warning_count",
        "warnings",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    source = report.get("source", {})
    for record in report.get("records", []):
        writer.writerow(
            {
                "source_kind": source.get("kind"),
                "source_label": source.get("label"),
                "input_format": report.get("input_format"),
            }
            | _flatten_analysis_record(record)
        )

    return output.getvalue()


def _render_batch_csv(report: dict) -> str:
    fieldnames = [
        "item",
        "operation",
        "status",
        "source_kind",
        "source_label",
        "accession",
        "database",
        "rettype",
        "retrieved_from",
        "saved_to",
        "error",
        "input_format",
        "sequence_id",
        "description",
        "molecule_type",
        "length",
        "gc_content",
        "at_content",
        "n_count",
        "ambiguous_count",
        "ambiguous_content",
        "melting_temp_tm",
        "molecular_weight",
        "isoelectric_point",
        "instability_index",
        "gravy",
        "aromaticity",
        "is_stable",
        "orfs_found",
        "longest_orf_frame",
        "longest_orf_aa",
        "longest_orf_translation_preview",
        "top_codons",
        "domains_found",
        "domain_names",
        "alphafold_model_id",
        "alphafold_avg_plddt",
        "restriction_hits",
        "kozak_hits",
        "cpg_dinucleotides",
        "custom_motif_hits",
        "custom_motifs",
        "warning_count",
        "warnings",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()

    for row in _batch_export_rows(report):
        writer.writerow(row)

    return output.getvalue()


def _render_annotation_markdown(report: dict) -> str:
    lines = [
        "# Annotation Report",
        "",
        f"- Source: {report['source']['kind']}",
        f"- Label: {report['source']['label']}",
        f"- Input format: {report['input_format']}",
        f"- Records: {report['record_count']}",
        "",
        "## Record Summary",
        "",
        "| Accession | ID | Type | Length | Organism | Features |",
        "|---|---|---|---:|---|---:|",
    ]

    for record in report["records"]:
        lines.append(
            f"| {record['accession']} | {record['sequence_id']} | {record['molecule_type']} | "
            f"{record['sequence_length']} | {record['organism']} | {record['feature_count']} |"
        )

    for record in report["records"]:
        lines.extend(
            [
                "",
                f"## {record['accession']}",
                "",
                f"- Description: {record['description']}",
                f"- Topology: {record['topology']}",
                f"- Date: {record['date']}",
                f"- Genes: {', '.join(record['gene_names']) or '-'}",
                f"- Products: {', '.join(record['product_names']) or '-'}",
                f"- Feature counts: {_feature_counts_summary(record['feature_counts']) or '-'}",
                "",
                "| Type | Location | Strand | Qualifiers |",
                "|---|---|---:|---|",
            ]
        )
        for feature in record["selected_features"]:
            lines.append(
                f"| {feature['type']} | {feature['location']} | "
                f"{feature['strand'] if feature['strand'] is not None else '-'} | "
                f"{_feature_qualifiers_summary(feature['qualifiers']) or '-'} |"
            )

    return "\n".join(lines) + "\n"


def _render_annotation_html(report: dict) -> str:
    record_rows = "\n".join(
        (
            "<tr>"
            f"<td>{escape(str(record['accession']))}</td>"
            f"<td>{escape(str(record['sequence_id']))}</td>"
            f"<td>{escape(str(record['molecule_type']))}</td>"
            f"<td>{escape(str(record['sequence_length']))}</td>"
            f"<td>{escape(str(record['organism']))}</td>"
            f"<td>{escape(str(record['feature_count']))}</td>"
            "</tr>"
        )
        for record in report["records"]
    )

    sections = []
    for record in report["records"]:
        feature_rows = "\n".join(
            (
                "<tr>"
                f"<td>{escape(str(feature['type']))}</td>"
                f"<td>{escape(str(feature['location']))}</td>"
                f"<td>{escape(str(feature['strand'] if feature['strand'] is not None else '-'))}"
                "</td>"
                f"<td>{escape(_feature_qualifiers_summary(feature['qualifiers']) or '-')}</td>"
                "</tr>"
            )
            for feature in record["selected_features"]
        )
        sections.append(
            f"""
            <section class="record-card">
              <h2>{escape(str(record["accession"]))}</h2>
              <p>{escape(str(record["description"]))}</p>
              <ul>
                <li><strong>Type:</strong> {escape(str(record["molecule_type"]))}</li>
                <li><strong>Length:</strong> {escape(str(record["sequence_length"]))}</li>
                <li><strong>Organism:</strong> {escape(str(record["organism"]))}</li>
                <li><strong>Genes:</strong> {escape(", ".join(record["gene_names"]) or "-")}</li>
                <li><strong>Products:</strong>
                  {escape(", ".join(record["product_names"]) or "-")}
                </li>
                <li><strong>Feature counts:</strong>
                  {escape(_feature_counts_summary(record["feature_counts"]) or "-")}
                </li>
              </ul>
              <table>
                <thead>
                  <tr><th>Type</th><th>Location</th><th>Strand</th><th>Qualifiers</th></tr>
                </thead>
                <tbody>
                  {feature_rows}
                </tbody>
              </table>
            </section>
            """
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Bio Toolkit Annotation Report</title>
  <style>
    :root {{
      --bg: #f5f1e8;
      --paper: #fffdf8;
      --ink: #172121;
      --muted: #5f6b6d;
      --accent: #0b6e4f;
      --line: #d8d0c1;
    }}
    body {{
      margin: 0;
      padding: 2rem;
      background: linear-gradient(180deg, #efe6d7 0%, var(--bg) 100%);
      color: var(--ink);
      font-family: "IBM Plex Sans", "Segoe UI", sans-serif;
    }}
    h1, h2 {{
      margin-top: 0;
      color: var(--accent);
    }}
    .shell {{
      max-width: 1100px;
      margin: 0 auto;
      display: grid;
      gap: 1.5rem;
    }}
    .panel, .record-card {{
      background: var(--paper);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 1.25rem 1.5rem;
      box-shadow: 0 10px 30px rgba(23, 33, 33, 0.08);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      margin-top: 1rem;
    }}
    th, td {{
      text-align: left;
      padding: 0.65rem 0.5rem;
      border-bottom: 1px solid var(--line);
      vertical-align: top;
    }}
    th {{
      color: var(--muted);
      font-weight: 600;
      letter-spacing: 0.02em;
    }}
    ul {{
      margin: 0.75rem 0 0;
      padding-left: 1.25rem;
    }}
  </style>
</head>
<body>
  <div class="shell">
    <section class="panel">
      <h1>Annotation Report</h1>
      <p><strong>Source:</strong> {escape(str(report["source"]["kind"]))}</p>
      <p><strong>Label:</strong> {escape(str(report["source"]["label"]))}</p>
      <p><strong>Input format:</strong> {escape(str(report["input_format"]))}</p>
      <p><strong>Records:</strong> {escape(str(report["record_count"]))}</p>
      <table>
        <thead>
          <tr><th>Accession</th><th>ID</th><th>Type</th><th>Length</th><th>Organism</th><th>Features</th></tr>
        </thead>
        <tbody>
          {record_rows}
        </tbody>
      </table>
    </section>
    {"".join(sections)}
  </div>
</body>
</html>
"""


def _feature_counts_summary(feature_counts: dict[str, int]) -> str:
    return "; ".join(f"{key}:{value}" for key, value in feature_counts.items())


def _flatten_analysis_record(record: dict) -> dict[str, object | None]:
    basic_stats = record.get("analysis", {}).get("basic_stats", {})
    motifs = record.get("analysis", {}).get("motifs", {})
    orfs = record.get("analysis", {}).get("orfs", {})
    domains = record.get("analysis", {}).get("domains", {})
    external = record.get("analysis", {}).get("external", {})
    alphafold = external.get("alphafold") or {}
    longest_orf = orfs.get("longest_orf") or {}
    custom_motifs = record.get("analysis", {}).get("custom_motifs", [])
    warnings = record.get("analysis", {}).get("warnings", [])

    return {
        "sequence_id": record.get("sequence_id"),
        "description": record.get("description"),
        "molecule_type": record.get("molecule_type"),
        "length": basic_stats.get("length"),
        "gc_content": basic_stats.get("gc_content"),
        "at_content": basic_stats.get("at_content"),
        "n_count": basic_stats.get("n_count"),
        "ambiguous_count": basic_stats.get("ambiguous_count"),
        "ambiguous_content": basic_stats.get("ambiguous_content"),
        "melting_temp_tm": basic_stats.get("melting_temp_tm"),
        "molecular_weight": basic_stats.get("molecular_weight"),
        "isoelectric_point": basic_stats.get("isoelectric_point"),
        "instability_index": basic_stats.get("instability_index"),
        "gravy": basic_stats.get("gravy"),
        "aromaticity": basic_stats.get("aromaticity"),
        "is_stable": basic_stats.get("is_stable"),
        "orfs_found": orfs.get("orfs_found"),
        "longest_orf_frame": longest_orf.get("frame"),
        "longest_orf_aa": longest_orf.get("length_aa"),
        "longest_orf_translation_preview": _translation_preview(
            longest_orf.get("protein_sequence")
        ),
        "top_codons": _codon_usage_summary(longest_orf.get("codon_usage") or {}),
        "domains_found": domains.get("domains_found"),
        "domain_names": _domain_summary(domains.get("all_domains") or []),
        "alphafold_model_id": alphafold.get("model_id"),
        "alphafold_avg_plddt": alphafold.get("avg_plddt"),
        "restriction_hits": len(motifs.get("restriction_sites", [])),
        "kozak_hits": len(motifs.get("kozak_sequences", [])),
        "cpg_dinucleotides": motifs.get("cpg_dinucleotides"),
        "custom_motif_hits": sum(int(item.get("count", 0)) for item in custom_motifs),
        "custom_motifs": _custom_motif_summary(custom_motifs),
        "warning_count": len(warnings),
        "warnings": "; ".join(str(item) for item in warnings),
    }


def _batch_export_rows(report: dict) -> list[dict[str, object | None]]:
    rows = []
    for item in report.get("results", []):
        base_row = {
            "item": item.get("item"),
            "operation": item.get("operation"),
            "status": item.get("status"),
            "source_kind": item.get("source_kind"),
            "source_label": item.get("label") or item.get("accession") or item.get("item"),
            "accession": item.get("accession"),
            "database": item.get("database"),
            "rettype": item.get("rettype"),
            "retrieved_from": item.get("retrieved_from"),
            "saved_to": item.get("saved_to"),
            "error": item.get("error"),
        }

        analysis = item.get("analysis", {})
        records = analysis.get("records", [])
        if item.get("operation") == "analyze" and item.get("status") == "ok" and records:
            for record in records:
                rows.append(
                    base_row
                    | {"input_format": analysis.get("input_format")}
                    | _flatten_analysis_record(record)
                )
            continue

        rows.append(base_row | {"input_format": item.get("input_format")})

    return rows


def _translation_preview(translation: object | None) -> str:
    if not translation:
        return ""
    text = str(translation)
    return text[:60] + ("..." if len(text) > 60 else "")


def _codon_usage_summary(codon_usage: dict[str, int]) -> str:
    return "; ".join(f"{codon}:{count}" for codon, count in list(codon_usage.items())[:5])


def _custom_motif_summary(custom_motifs: list[dict]) -> str:
    return "; ".join(
        f"{item.get('label')}({item.get('count')})"
        for item in custom_motifs
        if int(item.get("count", 0)) > 0
    )


def _domain_summary(domains: list[dict]) -> str:
    return "; ".join(str(item.get("name")) for item in domains[:5] if item.get("name"))


def _render_blast_delimited(report: dict, *, delimiter: str) -> str:
    fieldnames = [
        "rid",
        "program",
        "blast_database",
        "query_source",
        "query_label",
        "query_id",
        "subject_id",
        "percent_identity",
        "alignment_length",
        "mismatches",
        "gap_opens",
        "query_start",
        "query_end",
        "subject_start",
        "subject_end",
        "e_value",
        "bit_score",
        "query_coverage",
    ]
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=delimiter)
    writer.writeheader()

    for hit in report["hits"]:
        writer.writerow(
            {
                "rid": report["blast"]["rid"],
                "program": report["blast"]["program"],
                "blast_database": report["blast"]["database"],
                "query_source": report["source"]["kind"],
                "query_label": report["source"]["label"],
                "query_id": hit["query_id"],
                "subject_id": hit["subject_id"],
                "percent_identity": hit["percent_identity"],
                "alignment_length": hit["alignment_length"],
                "mismatches": hit["mismatches"],
                "gap_opens": hit["gap_opens"],
                "query_start": hit["query_start"],
                "query_end": hit["query_end"],
                "subject_start": hit["subject_start"],
                "subject_end": hit["subject_end"],
                "e_value": hit["e_value"],
                "bit_score": hit["bit_score"],
                "query_coverage": hit["query_coverage"],
            }
        )

    return output.getvalue()


def _feature_qualifiers_summary(qualifiers: dict[str, str]) -> str:
    return "; ".join(f"{key}={value}" for key, value in qualifiers.items())


def _selected_features_summary(selected_features: list[dict]) -> str:
    chunks = []
    for feature in selected_features:
        label = (
            feature["qualifiers"].get("gene")
            or feature["qualifiers"].get("product")
            or feature["location"]
        )
        chunks.append(f"{feature['type']}:{label}")
    return "; ".join(chunks)
