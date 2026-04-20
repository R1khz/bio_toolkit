from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord

from bio_toolkit.analysis import detect_molecule_type


def build_annotation_report(
    *,
    records: list[SeqRecord],
    input_format: str,
    source_info: dict[str, str],
    feature_limit: int = 10,
) -> dict[str, Any]:
    if feature_limit < 1:
        raise ValueError("Feature limit must be at least 1.")

    annotated_records = [
        extract_record_annotation(record, input_format=input_format, feature_limit=feature_limit)
        for record in records
    ]
    return {
        "source": source_info,
        "input_format": input_format,
        "record_count": len(annotated_records),
        "feature_limit": feature_limit,
        "records": annotated_records,
    }


def extract_record_annotation(
    record: SeqRecord,
    *,
    input_format: str,
    feature_limit: int = 10,
) -> dict[str, Any]:
    annotations = record.annotations
    feature_counts = Counter(feature.type for feature in record.features)
    selected_features = _selected_features(record.features, limit=feature_limit)

    accession_list = annotations.get("accessions") or []
    accession = accession_list[0] if accession_list else record.id
    keywords = [str(item) for item in annotations.get("keywords", []) if str(item).strip()]
    taxonomy = [str(item) for item in annotations.get("taxonomy", []) if str(item).strip()]
    genes = _qualifier_values(record.features, "gene")
    products = _qualifier_values(record.features, "product")

    return {
        "sequence_id": record.id,
        "accession": accession,
        "description": record.description,
        "input_format": input_format,
        "molecule_type": str(annotations.get("molecule_type") or detect_molecule_type(record)),
        "sequence_length": len(record.seq),
        "organism": str(annotations.get("organism") or annotations.get("source") or "-"),
        "taxonomy": taxonomy,
        "keywords": keywords,
        "topology": str(annotations.get("topology") or "-"),
        "date": str(annotations.get("date") or "-"),
        "source": str(annotations.get("source") or "-"),
        "gene_names": genes,
        "product_names": products,
        "feature_count": len(record.features),
        "feature_counts": dict(sorted(feature_counts.items(), key=lambda item: (-item[1], item[0]))),
        "selected_features": selected_features,
    }


def default_annotation_export_path(output_dir: Path, label: str, export_format: str) -> Path:
    safe_label = _safe_label(label)
    suffix = {
        "json": ".json",
        "csv": ".csv",
        "markdown": ".md",
        "html": ".html",
    }[export_format]
    return output_dir / f"{safe_label}.annotations{suffix}"


def _selected_features(features: list[SeqFeature], *, limit: int) -> list[dict[str, Any]]:
    interesting = [feature for feature in features if feature.type != "source"]
    chosen = interesting[:limit] if interesting else features[:limit]
    return [summarize_feature(feature) for feature in chosen]


def summarize_feature(feature: SeqFeature) -> dict[str, Any]:
    strand = getattr(feature.location, "strand", None)
    qualifiers = {
        key: _join_qualifier_values(values)
        for key, values in feature.qualifiers.items()
        if key in {"gene", "product", "locus_tag", "protein_id", "note"}
    }
    return {
        "type": feature.type,
        "location": str(feature.location),
        "strand": strand,
        "qualifiers": qualifiers,
    }


def _qualifier_values(features: list[SeqFeature], key: str) -> list[str]:
    values: list[str] = []
    for feature in features:
        if key not in feature.qualifiers:
            continue
        values.extend(str(item) for item in feature.qualifiers[key] if str(item).strip())
    seen: set[str] = set()
    unique_values = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        unique_values.append(value)
    return unique_values


def _join_qualifier_values(values: list[Any]) -> str:
    cleaned = [str(item).strip() for item in values if str(item).strip()]
    return "; ".join(cleaned)


def _safe_label(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
