from __future__ import annotations

from typing import Any


def compare_sequence_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    if len(records) < 2:
        raise ValueError("Comparison requires at least two analyzed records.")

    molecule_types = sorted({str(record["molecule_type"]) for record in records})
    lengths = [int(record["analysis"]["basic_stats"].get("length", 0)) for record in records]

    nucleotide_records = [record for record in records if record["molecule_type"] in {"DNA", "RNA"}]
    protein_records = [record for record in records if record["molecule_type"] == "PROTEIN"]

    result: dict[str, Any] = {
        "record_count": len(records),
        "molecule_types": molecule_types,
        "all_same_molecule_type": len(molecule_types) == 1,
        "length": _range_summary(lengths),
        "nucleotide": None,
        "protein": None,
    }

    if nucleotide_records:
        gc_values = [
            float(record["analysis"]["basic_stats"].get("gc_content", 0.0))
            for record in nucleotide_records
        ]
        orf_counts = [
            int(record["analysis"]["orfs"].get("orfs_found", 0)) for record in nucleotide_records
        ]
        restriction_counts = [
            len(record["analysis"]["motifs"].get("restriction_sites", []))
            for record in nucleotide_records
        ]
        cpg_counts = [
            int(record["analysis"]["motifs"].get("cpg_dinucleotides", 0))
            for record in nucleotide_records
        ]
        result["nucleotide"] = {
            "record_count": len(nucleotide_records),
            "gc_content": _range_summary(gc_values),
            "orf_count": _range_summary(orf_counts),
            "restriction_site_hits": _range_summary(restriction_counts),
            "cpg_dinucleotides": _range_summary(cpg_counts),
        }

    if protein_records:
        molecular_weight_values = [
            value
            for value in (
                record["analysis"]["basic_stats"].get("molecular_weight")
                for record in protein_records
            )
            if isinstance(value, (int, float))
        ]
        pi_values = [
            value
            for value in (
                record["analysis"]["basic_stats"].get("isoelectric_point")
                for record in protein_records
            )
            if isinstance(value, (int, float))
        ]
        instability_values = [
            value
            for value in (
                record["analysis"]["basic_stats"].get("instability_index")
                for record in protein_records
            )
            if isinstance(value, (int, float))
        ]
        result["protein"] = {
            "record_count": len(protein_records),
            "molecular_weight": _range_summary(molecular_weight_values),
            "isoelectric_point": _range_summary(pi_values),
            "instability_index": _range_summary(instability_values),
        }

    return result


def _range_summary(values: list[int | float]) -> dict[str, int | float] | None:
    if not values:
        return None

    minimum = min(values)
    maximum = max(values)
    delta = maximum - minimum

    return {
        "min": round(minimum, 4) if isinstance(minimum, float) else minimum,
        "max": round(maximum, 4) if isinstance(maximum, float) else maximum,
        "delta": round(delta, 4) if isinstance(delta, float) else delta,
    }
