from __future__ import annotations

from typing import Any


def build_analysis_warnings(
    *,
    sequence: str,
    molecule_type: str,
    basic_stats: dict[str, Any],
    motifs: dict[str, Any],
    orfs: dict[str, Any],
    min_orf_aa: int,
) -> list[str]:
    warnings = []
    raw_sequence = sequence.upper()
    length = int(basic_stats.get("length", 0) or 0)

    if molecule_type in {"DNA", "RNA"}:
        n_count = int(basic_stats.get("n_count", 0) or 0)
        ambiguous_count = int(basic_stats.get("ambiguous_count", 0) or 0)
        ambiguous_content = basic_stats.get("ambiguous_content")

        if length < 30:
            warnings.append("Sequence is short; motif and ORF signals may be limited.")
        if n_count > 0:
            warnings.append(f"Sequence contains {n_count} unresolved bases (N).")
        if ambiguous_count > 0:
            warnings.append(
                "Sequence contains ambiguous IUPAC bases "
                f"({ambiguous_count}, {ambiguous_content}%)."
            )
        if length >= max(min_orf_aa * 3, 90) and not orfs.get("orfs_found"):
            warnings.append("No ORFs passed the current threshold; lower --min-orf-aa if needed.")
        if length >= 200 and int(motifs.get("cpg_dinucleotides", 0) or 0) == 0:
            warnings.append("No CpG dinucleotides were detected in this sequence.")
    elif molecule_type == "PROTEIN":
        ambiguous_residues = raw_sequence.count("X")
        stop_symbols = raw_sequence.count("*")

        if length < 30:
            warnings.append("Protein is short; physicochemical metrics may be less stable.")
        if ambiguous_residues > 0:
            warnings.append(f"Protein contains {ambiguous_residues} ambiguous residues (X).")
        if stop_symbols > 0:
            warnings.append(f"Protein contains {stop_symbols} stop symbols (*).")

        instability = basic_stats.get("instability_index")
        if isinstance(instability, (int, float)) and instability >= 40:
            warnings.append("Protein is predicted to be unstable by instability index.")
    else:
        warnings.append("Sequence type could not be determined reliably.")

    return warnings
