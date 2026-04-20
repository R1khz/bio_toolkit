from __future__ import annotations

from io import StringIO
from pathlib import Path

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

SUPPORTED_INPUT_FORMATS = {"auto", "fasta", "genbank", "gb"}
FASTA_SUFFIXES = {".fasta", ".fa", ".fna", ".faa", ".ffn", ".frn"}
GENBANK_SUFFIXES = {".gb", ".gbk", ".genbank"}


class SequenceIOError(RuntimeError):
    """Raised when sequence input cannot be parsed."""


def load_records_from_path(path: Path, input_format: str = "auto") -> tuple[list[SeqRecord], str]:
    if not path.exists():
        raise SequenceIOError(f"Input file was not found: {path}")

    resolved_format = detect_input_format(
        input_format=input_format,
        path=path,
        text=path.read_text(encoding="utf-8"),
    )
    return _parse_records(path.read_text(encoding="utf-8"), resolved_format), resolved_format


def load_records_from_text(text: str, input_format: str = "auto") -> tuple[list[SeqRecord], str]:
    resolved_format = detect_input_format(input_format=input_format, text=text)
    return _parse_records(text, resolved_format), resolved_format


def detect_input_format(
    *,
    input_format: str = "auto",
    path: Path | None = None,
    text: str = "",
) -> str:
    normalized = input_format.strip().lower()
    if normalized not in SUPPORTED_INPUT_FORMATS:
        allowed = ", ".join(sorted(SUPPORTED_INPUT_FORMATS))
        raise SequenceIOError(f"Unsupported input format '{input_format}'. Use one of: {allowed}.")

    if normalized in {"fasta", "genbank"}:
        return normalized
    if normalized == "gb":
        return "genbank"

    if path is not None:
        suffix = path.suffix.lower()
        if suffix in FASTA_SUFFIXES:
            return "fasta"
        if suffix in GENBANK_SUFFIXES:
            return "genbank"

    stripped = text.lstrip()
    if stripped.startswith(">"):
        return "fasta"
    if stripped.startswith("LOCUS"):
        return "genbank"

    raise SequenceIOError(
        "Could not detect input format automatically. Use --input-format fasta or --input-format genbank."
    )


def format_from_rettype(rettype: str) -> str:
    return "genbank" if rettype.strip().lower() in {"gb", "genbank"} else "fasta"


def dump_records_to_text(records: list[SeqRecord], output_format: str = "fasta") -> str:
    normalized = output_format.strip().lower()
    if normalized not in {"fasta", "genbank"}:
        raise SequenceIOError("Unsupported output format. Use one of: fasta, genbank.")

    handle = StringIO()
    try:
        written = SeqIO.write(records, handle, normalized)
    except Exception as exc:
        raise SequenceIOError(f"Failed to serialize records as {normalized}: {exc}") from exc

    if written == 0:
        raise SequenceIOError("No sequence records were available to serialize.")

    return handle.getvalue()


def _parse_records(text: str, resolved_format: str) -> list[SeqRecord]:
    handle = StringIO(text)
    try:
        records = list(SeqIO.parse(handle, resolved_format))
    except Exception as exc:
        raise SequenceIOError(f"Failed to parse {resolved_format} content: {exc}") from exc

    if not records:
        raise SequenceIOError(f"No sequence records were found in the {resolved_format} input.")

    return records
