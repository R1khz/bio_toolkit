from __future__ import annotations

import csv
import json
from html import escape
from io import StringIO

SUPPORTED_EXPORT_FORMATS = {"json", "csv", "markdown", "html"}
SUPPORTED_BLAST_EXPORT_FORMATS = {"json", "csv", "tsv"}


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
        raise ValueError(f"Unsupported BLAST export format '{export_format}'. Use one of: {allowed}.")
    return normalized


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
                f"<td>{escape(str(feature['strand'] if feature['strand'] is not None else '-'))}</td>"
                f"<td>{escape(_feature_qualifiers_summary(feature['qualifiers']) or '-')}</td>"
                "</tr>"
            )
            for feature in record["selected_features"]
        )
        sections.append(
            f"""
            <section class="record-card">
              <h2>{escape(str(record['accession']))}</h2>
              <p>{escape(str(record['description']))}</p>
              <ul>
                <li><strong>Type:</strong> {escape(str(record['molecule_type']))}</li>
                <li><strong>Length:</strong> {escape(str(record['sequence_length']))}</li>
                <li><strong>Organism:</strong> {escape(str(record['organism']))}</li>
                <li><strong>Genes:</strong> {escape(', '.join(record['gene_names']) or '-')}</li>
                <li><strong>Products:</strong> {escape(', '.join(record['product_names']) or '-')}</li>
                <li><strong>Feature counts:</strong> {escape(_feature_counts_summary(record['feature_counts']) or '-')}</li>
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
      <p><strong>Source:</strong> {escape(str(report['source']['kind']))}</p>
      <p><strong>Label:</strong> {escape(str(report['source']['label']))}</p>
      <p><strong>Input format:</strong> {escape(str(report['input_format']))}</p>
      <p><strong>Records:</strong> {escape(str(report['record_count']))}</p>
      <table>
        <thead>
          <tr><th>Accession</th><th>ID</th><th>Type</th><th>Length</th><th>Organism</th><th>Features</th></tr>
        </thead>
        <tbody>
          {record_rows}
        </tbody>
      </table>
    </section>
    {''.join(sections)}
  </div>
</body>
</html>
"""


def _feature_counts_summary(feature_counts: dict[str, int]) -> str:
    return "; ".join(f"{key}:{value}" for key, value in feature_counts.items())


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
        label = feature["qualifiers"].get("gene") or feature["qualifiers"].get("product") or feature["location"]
        chunks.append(f"{feature['type']}:{label}")
    return "; ".join(chunks)
