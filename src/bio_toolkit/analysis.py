from __future__ import annotations

import re
from typing import Any

from Bio.Seq import Seq
from Bio.SeqFeature import SeqFeature
from Bio.SeqRecord import SeqRecord
from Bio.SeqUtils import gc_fraction
from Bio.SeqUtils.MeltingTemp import Tm_Wallace
from Bio.SeqUtils.ProtParam import ProteinAnalysis

VALID_DNA_CHARS = set("ATCGNRYSWKMBDHVN-")
VALID_RNA_CHARS = set("AUCGNRYSWKMBDHVN-")
VALID_PROT_CHARS = set("ACDEFGHIKLMNPQRSTVWYBZX*-")
AMBIGUOUS_NUCLEOTIDE_CHARS = "NRYSWKMBDHV"

RESTRICTION_SITES = {
    "EcoRI": "GAATTC",
    "BamHI": "GGATCC",
    "HindIII": "AAGCTT",
    "NotI": "GCGGCCGC",
    "XhoI": "CTCGAG",
    "NcoI": "CCATGG",
    "SalI": "GTCGAC",
    "XbaI": "TCTAGA",
    "SphI": "GCATGC",
    "PstI": "CTGCAG",
    "SmaI": "CCCGGG",
    "KpnI": "GGTACC",
    "SacI": "GAGCTC",
    "ClaI": "ATCGAT",
    "NheI": "GCTAGC",
}

PROTEIN_DOMAIN_SIGNATURES = [
    {
        "name": "P-loop NTP-binding domain",
        "pattern": r"[AGX][A-Z]{4}GK[ST]",
        "note": "Walker A / P-loop-like signature",
    },
    {
        "name": "C2H2 zinc finger domain",
        "pattern": r"C.{2,4}C.{8,15}H.{3,5}H",
        "note": "C2H2-like zinc finger signature",
    },
    {
        "name": "EF-hand calcium-binding domain",
        "pattern": r"D.{1,3}D.{8,12}E",
        "note": "EF-hand-like acidic loop",
    },
    {
        "name": "Leucine zipper region",
        "pattern": r"L.{6}L.{6}L.{6}L",
        "note": "Leucine zipper-like heptad repeat",
    },
]


class SequenceAnalyzer:
    def __init__(self, *, min_orf_aa: int = 30, custom_motifs: list[str] | None = None) -> None:
        self.min_orf_aa = min_orf_aa
        self.custom_motifs = [motif.strip() for motif in (custom_motifs or []) if motif.strip()]

    def analyze_records(self, records: list[SeqRecord]) -> list[dict[str, Any]]:
        return [self.analyze_record(record) for record in records]

    def analyze_record(self, record: SeqRecord) -> dict[str, Any]:
        molecule_type = detect_molecule_type(record)
        basic_stats = self._basic_stats(record, molecule_type)
        custom_motif_hits = self._custom_motif_analysis(record)
        result = {
            "sequence_id": record.id,
            "description": record.description,
            "molecule_type": molecule_type,
            "analysis": {
                "basic_stats": basic_stats,
                "custom_motifs": custom_motif_hits,
            },
        }

        if molecule_type in {"DNA", "RNA"}:
            result["analysis"]["motifs"] = self._motif_analysis(record)
            result["analysis"]["orfs"] = self._orf_analysis(record)
            result["analysis"]["domains"] = {
                "skipped": True,
                "reason": (
                    "Protein domain analysis does not apply to "
                    f"{molecule_type.lower()} sequences."
                ),
            }
        elif molecule_type == "PROTEIN":
            result["analysis"]["motifs"] = {
                "skipped": True,
                "reason": f"Motif analysis does not apply to {molecule_type.lower()} sequences.",
            }
            result["analysis"]["orfs"] = {
                "skipped": True,
                "reason": f"ORF analysis does not apply to {molecule_type.lower()} sequences.",
            }
            result["analysis"]["domains"] = self._protein_domain_analysis(record)
        else:
            result["analysis"]["motifs"] = {
                "skipped": True,
                "reason": "Motif analysis does not apply to unknown sequences.",
            }
            result["analysis"]["orfs"] = {
                "skipped": True,
                "reason": "ORF analysis does not apply to unknown sequences.",
            }
            result["analysis"]["domains"] = {
                "skipped": True,
                "reason": "Protein domain analysis does not apply to unknown sequences.",
            }

        result["analysis"]["warnings"] = self._analysis_warnings(
            record=record,
            molecule_type=molecule_type,
            basic_stats=basic_stats,
            motifs=result["analysis"]["motifs"],
            orfs=result["analysis"]["orfs"],
        )

        return result

    def _basic_stats(self, record: SeqRecord, molecule_type: str) -> dict[str, Any]:
        if molecule_type == "PROTEIN":
            return _analyze_protein(record)
        return _analyze_nucleotide(record)

    def _motif_analysis(self, record: SeqRecord) -> dict[str, Any]:
        seq = _normalized_nucleotide(record)
        restriction_sites = []
        for enzyme, pattern in RESTRICTION_SITES.items():
            positions = [match.start() for match in re.finditer(f"(?={pattern})", seq)]
            if positions:
                restriction_sites.append(
                    {
                        "enzyme": enzyme,
                        "pattern": pattern,
                        "positions": positions,
                        "count": len(positions),
                    }
                )

        kozak_pattern = r"GCC[AG]CCATGG"
        kozak_sequences = [
            {"position": match.start(), "sequence": match.group()}
            for match in re.finditer(kozak_pattern, seq)
        ]

        return {
            "restriction_sites": restriction_sites,
            "kozak_sequences": kozak_sequences,
            "cpg_dinucleotides": seq.count("CG"),
            "cpg_islands_approx": _count_cpg_islands(seq),
        }

    def _custom_motif_analysis(self, record: SeqRecord) -> list[dict[str, Any]]:
        if not self.custom_motifs:
            return []

        sequence = str(record.seq).upper()
        results = []
        for motif in self.custom_motifs:
            if motif.lower().startswith("re:"):
                pattern = motif[3:]
                try:
                    positions = [match.start() for match in re.finditer(f"(?={pattern})", sequence)]
                except re.error as exc:
                    raise ValueError(f"Invalid custom motif regex '{motif}': {exc}") from exc
                match_type = "regex"
            else:
                pattern = motif.upper()
                positions = [
                    match.start()
                    for match in re.finditer(f"(?={re.escape(pattern)})", sequence)
                ]
                match_type = "literal"

            results.append(
                {
                    "label": motif,
                    "pattern": pattern,
                    "match_type": match_type,
                    "positions": positions,
                    "count": len(positions),
                }
            )

        return results

    def _orf_analysis(self, record: SeqRecord) -> dict[str, Any]:
        seq = Seq(_normalized_nucleotide(record))
        reverse = seq.reverse_complement()
        frames = [
            (seq, "+1", 0),
            (seq[1:], "+2", 1),
            (seq[2:], "+3", 2),
            (reverse, "-1", 0),
            (reverse[1:], "-2", 1),
            (reverse[2:], "-3", 2),
        ]

        orfs = []
        for frame_seq, frame_name, offset in frames:
            aa_sequence = _translate_frame(frame_seq)
            start = 0
            while True:
                methionine_index = aa_sequence.find("M", start)
                if methionine_index == -1:
                    break

                stop_index = aa_sequence.find("*", methionine_index)
                if stop_index == -1:
                    break

                protein = aa_sequence[methionine_index:stop_index]
                if len(protein) >= self.min_orf_aa:
                    coding_sequence = str(
                        frame_seq[methionine_index * 3 : stop_index * 3]
                    ).upper()
                    orfs.append(
                        {
                            "frame": frame_name,
                            "start_nt": methionine_index * 3 + offset,
                            "end_nt": stop_index * 3 + offset,
                            "length_aa": len(protein),
                            "protein_sequence": protein,
                            "protein_preview": protein[:50] + ("..." if len(protein) > 50 else ""),
                            "coding_sequence": coding_sequence,
                            "codon_usage": _codon_usage(coding_sequence),
                        }
                    )

                start = methionine_index + 1

        sorted_orfs = sorted(orfs, key=lambda item: item["length_aa"], reverse=True)
        return {
            "orfs_found": len(sorted_orfs),
            "longest_orf": sorted_orfs[0] if sorted_orfs else None,
            "all_orfs": sorted_orfs[:10],
            "min_orf_aa": self.min_orf_aa,
        }

    def _analysis_warnings(
        self,
        *,
        record: SeqRecord,
        molecule_type: str,
        basic_stats: dict[str, Any],
        motifs: dict[str, Any],
        orfs: dict[str, Any],
    ) -> list[str]:
        warnings = []
        raw_sequence = str(record.seq).upper()
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
            if length >= max(self.min_orf_aa * 3, 90) and not orfs.get("orfs_found"):
                warnings.append(
                    "No ORFs passed the current threshold; lower --min-orf-aa if needed."
                )
            if length >= 200 and int(motifs.get("cpg_dinucleotides", 0) or 0) == 0:
                warnings.append("No CpG dinucleotides were detected in this sequence.")
        elif molecule_type == "PROTEIN":
            ambiguous_residues = raw_sequence.count("X")
            stop_symbols = raw_sequence.count("*")

            if length < 30:
                warnings.append("Protein is short; physicochemical metrics may be less stable.")
            if ambiguous_residues > 0:
                warnings.append(
                    f"Protein contains {ambiguous_residues} ambiguous residues (X)."
                )
            if stop_symbols > 0:
                warnings.append(f"Protein contains {stop_symbols} stop symbols (*).")

            instability = basic_stats.get("instability_index")
            if isinstance(instability, (int, float)) and instability >= 40:
                warnings.append("Protein is predicted to be unstable by instability index.")
        else:
            warnings.append("Sequence type could not be determined reliably.")

        return warnings

    def _protein_domain_analysis(self, record: SeqRecord) -> dict[str, Any]:
        feature_domains = _feature_domains(record.features)
        signature_domains = _signature_domains(str(record.seq).upper())
        all_domains = feature_domains + signature_domains

        return {
            "domains_found": len(all_domains),
            "feature_domains": len(feature_domains),
            "signature_domains": len(signature_domains),
            "all_domains": all_domains[:10],
        }


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


def detect_molecule_type(record: SeqRecord) -> str:
    sequence = str(record.seq).upper().replace("-", "").replace("N", "")
    chars = set(sequence)
    if not chars:
        return "UNKNOWN"
    if chars <= VALID_RNA_CHARS and "U" in chars:
        return "RNA"
    if chars <= VALID_DNA_CHARS:
        return "DNA"
    if chars <= VALID_PROT_CHARS:
        return "PROTEIN"
    return "UNKNOWN"


def _analyze_nucleotide(record: SeqRecord) -> dict[str, Any]:
    sequence = str(record.seq).upper()
    length = len(sequence)
    composition = {base: sequence.count(base) for base in "ATCGU"}
    ambiguous_bases = {
        base: sequence.count(base)
        for base in AMBIGUOUS_NUCLEOTIDE_CHARS
        if sequence.count(base) > 0
    }
    informative_length = max(length - sequence.count("-"), 0)
    ambiguous_count = sum(ambiguous_bases.values())
    gc_content = round(gc_fraction(record.seq) * 100, 2)

    result: dict[str, Any] = {
        "length": length,
        "gc_content": gc_content,
        "at_content": round(100 - gc_content, 2),
        "base_composition": {base: count for base, count in composition.items() if count > 0},
        "n_count": sequence.count("N"),
        "ambiguous_bases": ambiguous_bases,
        "ambiguous_count": ambiguous_count,
        "ambiguous_content": round(
            (ambiguous_count / informative_length) * 100, 2
        )
        if informative_length
        else 0.0,
    }

    if length <= 10_000 and "N" not in sequence and set(sequence) <= set("ATCG"):
        try:
            result["melting_temp_tm"] = round(float(Tm_Wallace(record.seq)), 2)
        except Exception:
            result["melting_temp_tm"] = None

    return result


def _analyze_protein(record: SeqRecord) -> dict[str, Any]:
    sequence = str(record.seq).upper().replace("*", "")
    clean_sequence = _clean_protein_sequence(sequence)
    result: dict[str, Any] = {
        "length": len(sequence),
        "amino_acid_count": _amino_acid_composition(sequence),
    }

    if clean_sequence:
        try:
            analysis = ProteinAnalysis(clean_sequence)
            instability = analysis.instability_index()
            result["molecular_weight"] = round(analysis.molecular_weight(), 2)
            result["isoelectric_point"] = round(analysis.isoelectric_point(), 2)
            result["instability_index"] = round(instability, 2)
            result["gravy"] = round(analysis.gravy(), 4)
            result["aromaticity"] = round(analysis.aromaticity(), 4)
            result["is_stable"] = instability < 40
        except Exception:
            pass

    return result


def _feature_domains(features: list[SeqFeature]) -> list[dict[str, Any]]:
    domains = []
    interesting_types = {"region", "domain", "repeat_region", "motif", "site"}

    for feature in features:
        feature_type = str(feature.type).lower()
        if feature_type not in interesting_types:
            continue

        qualifiers = feature.qualifiers
        name = (
            _first_non_empty(
                qualifiers.get("region_name", []),
                qualifiers.get("standard_name", []),
                qualifiers.get("note", []),
                qualifiers.get("product", []),
            )
            or str(feature.type)
        )
        sequence = ""
        if getattr(feature, "location", None) is not None:
            start_aa = int(feature.location.start) + 1
            end_aa = int(feature.location.end)
        else:
            start_aa = 0
            end_aa = 0

        domains.append(
            {
                "name": name,
                "start_aa": start_aa,
                "end_aa": end_aa,
                "source": "feature",
                "evidence": str(feature.type),
                "sequence": sequence,
            }
        )

    return domains


def _signature_domains(sequence: str) -> list[dict[str, Any]]:
    clean_sequence = _clean_protein_sequence(sequence)
    domains = []

    for signature in PROTEIN_DOMAIN_SIGNATURES:
        for match in re.finditer(signature["pattern"], clean_sequence):
            domains.append(
                {
                    "name": signature["name"],
                    "start_aa": match.start() + 1,
                    "end_aa": match.end(),
                    "source": "signature",
                    "evidence": signature["note"],
                    "sequence": match.group(),
                }
            )

    return domains


def _amino_acid_composition(sequence: str) -> dict[str, int]:
    aa_names = {
        "A": "Ala",
        "R": "Arg",
        "N": "Asn",
        "D": "Asp",
        "C": "Cys",
        "E": "Glu",
        "Q": "Gln",
        "G": "Gly",
        "H": "His",
        "I": "Ile",
        "L": "Leu",
        "K": "Lys",
        "M": "Met",
        "F": "Phe",
        "P": "Pro",
        "S": "Ser",
        "T": "Thr",
        "W": "Trp",
        "Y": "Tyr",
        "V": "Val",
    }
    return {
        name: sequence.count(code) for code, name in aa_names.items() if sequence.count(code) > 0
    }


def _clean_protein_sequence(sequence: str) -> str:
    valid = set("ACDEFGHIKLMNPQRSTVWY")
    return "".join(amino_acid for amino_acid in sequence if amino_acid in valid)


def _first_non_empty(*values: list[Any]) -> str:
    for bucket in values:
        for item in bucket:
            text = str(item).strip()
            if text:
                return text
    return ""


def _normalized_nucleotide(record: SeqRecord) -> str:
    return str(record.seq).upper().replace("U", "T")


def _count_cpg_islands(sequence: str) -> int:
    window = 200
    islands = 0
    in_island = False

    for start in range(0, len(sequence) - window, 50):
        chunk = sequence[start : start + window]
        if len(chunk) < window:
            break

        gc_ratio = (chunk.count("G") + chunk.count("C")) / window
        cpg_ratio = chunk.count("CG") / window
        if gc_ratio > 0.5 and cpg_ratio > 0.6:
            if not in_island:
                islands += 1
                in_island = True
        else:
            in_island = False

    return islands


def _translate_frame(sequence: Seq) -> str:
    usable_length = len(sequence) - (len(sequence) % 3)
    if usable_length <= 0:
        return ""
    return str(sequence[:usable_length].translate(to_stop=False))


def _codon_usage(sequence: str) -> dict[str, int]:
    codons = [
        sequence[index : index + 3]
        for index in range(0, len(sequence), 3)
        if len(sequence[index : index + 3]) == 3
    ]
    counts: dict[str, int] = {}
    for codon in codons:
        counts[codon] = counts.get(codon, 0) + 1
    return dict(sorted(counts.items(), key=lambda item: (-item[1], item[0])))


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
