from __future__ import annotations

from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from bio_toolkit.domain.analysis import detect_molecule_type

SUPPORTED_TRANSFORMS = {
    "reverse-complement",
    "reverse_complement",
    "revcomp",
    "translate",
    "subseq",
}


class TransformError(RuntimeError):
    """Raised when a sequence transform cannot be completed."""


def normalize_transform_name(operation: str) -> str:
    normalized = operation.strip().lower().replace("_", "-")
    if normalized == "revcomp":
        normalized = "reverse-complement"
    if normalized not in {"reverse-complement", "translate", "subseq"}:
        allowed = ", ".join(sorted({"reverse-complement", "translate", "subseq"}))
        raise TransformError(f"Unsupported transform '{operation}'. Use one of: {allowed}.")
    return normalized


def transform_records(
    *,
    records: list[SeqRecord],
    operation: str,
    frame: int = 1,
    to_stop: bool = False,
    start: int = 1,
    end: int | None = None,
) -> tuple[list[SeqRecord], dict]:
    normalized = normalize_transform_name(operation)

    if normalized == "reverse-complement":
        transformed = [reverse_complement_record(record) for record in records]
        metadata = {"operation": normalized}
    elif normalized == "translate":
        transformed = [translate_record(record, frame=frame, to_stop=to_stop) for record in records]
        metadata = {"operation": normalized, "frame": frame, "to_stop": to_stop}
    else:
        transformed = [subsequence_record(record, start=start, end=end) for record in records]
        metadata = {"operation": normalized, "start": start, "end": end}

    return transformed, metadata


def reverse_complement_record(record: SeqRecord) -> SeqRecord:
    molecule_type = detect_molecule_type(record)
    if molecule_type not in {"DNA", "RNA"}:
        raise TransformError("Reverse complement only applies to DNA or RNA sequences.")

    sequence = str(record.seq).upper()
    if molecule_type == "RNA":
        transformed_seq = Seq(sequence.replace("U", "T")).reverse_complement().transcribe()
    else:
        transformed_seq = Seq(sequence).reverse_complement()

    return SeqRecord(
        transformed_seq,
        id=f"{record.id}|revcomp",
        name=f"{record.name}|revcomp" if record.name else f"{record.id}|revcomp",
        description=f"reverse-complement of {record.description or record.id}",
    )


def translate_record(record: SeqRecord, *, frame: int = 1, to_stop: bool = False) -> SeqRecord:
    molecule_type = detect_molecule_type(record)
    if molecule_type not in {"DNA", "RNA"}:
        raise TransformError("Translate only applies to DNA or RNA sequences.")
    if frame not in {1, 2, 3}:
        raise TransformError("Translation frame must be 1, 2, or 3.")

    sequence = Seq(str(record.seq).upper().replace("U", "T"))
    translated = sequence[frame - 1 :].translate(to_stop=to_stop)
    return SeqRecord(
        translated,
        id=f"{record.id}|aa_f{frame}",
        name=f"{record.name}|aa_f{frame}" if record.name else f"{record.id}|aa_f{frame}",
        description=f"translation frame {frame} of {record.description or record.id}",
    )


def subsequence_record(record: SeqRecord, *, start: int = 1, end: int | None = None) -> SeqRecord:
    if start < 1:
        raise TransformError("Subsequence start must be 1 or greater.")

    sequence = str(record.seq)
    resolved_end = len(sequence) if end in (None, 0) else end
    if resolved_end < start:
        raise TransformError("Subsequence end must be greater than or equal to start.")
    if resolved_end > len(sequence):
        raise TransformError("Subsequence end exceeds the sequence length.")

    sliced = Seq(sequence[start - 1 : resolved_end])
    return SeqRecord(
        sliced,
        id=f"{record.id}|subseq_{start}_{resolved_end}",
        name=f"{record.name}|subseq_{start}_{resolved_end}"
        if record.name
        else f"{record.id}|subseq_{start}_{resolved_end}",
        description=f"subsequence {start}-{resolved_end} of {record.description or record.id}",
    )


def default_transform_path(output_dir: Path, label: str, operation: str) -> Path:
    safe_label = _safe_transform_label(label)
    safe_operation = normalize_transform_name(operation).replace("-", "_")
    return output_dir / f"{safe_label}.{safe_operation}.fasta"


def _safe_transform_label(value: str) -> str:
    return "".join(char if char.isalnum() or char in "._-" else "_" for char in value.strip())
