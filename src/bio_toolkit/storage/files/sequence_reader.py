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

    text = _read_text_prefix(path) if _requires_text_detection(input_format, path=path) else ""
    resolved_format = detect_input_format(input_format=input_format, path=path, text=text)
    return _parse_records_from_path(path, resolved_format), resolved_format


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
        "Could not detect input format automatically. Use --input-format fasta or "
        "--input-format genbank."
    )


def _requires_text_detection(input_format: str, path: Path | None = None) -> bool:
    normalized = input_format.strip().lower()
    if normalized in {"fasta", "genbank", "gb"}:
        return False

    if path is not None:
        suffix = path.suffix.lower()
        if suffix in FASTA_SUFFIXES or suffix in GENBANK_SUFFIXES:
            return False

    return True


def _read_text_prefix(path: Path, *, prefix_size: int = 4096) -> str:
    with path.open("r", encoding="utf-8") as handle:
        return handle.read(prefix_size)


def _parse_records_from_path(path: Path, resolved_format: str) -> list[SeqRecord]:
    with path.open("r", encoding="utf-8") as handle:
        try:
            records = list(SeqIO.parse(handle, resolved_format))
        except Exception as exc:
            raise SequenceIOError(f"Failed to parse {resolved_format} content: {exc}") from exc

    if not records:
        raise SequenceIOError(f"No sequence records were found in the {resolved_format} input.")

    return records


def _parse_records(text: str, resolved_format: str) -> list[SeqRecord]:
    handle = StringIO(text)
    try:
        records = list(SeqIO.parse(handle, resolved_format))
    except Exception as exc:
        raise SequenceIOError(f"Failed to parse {resolved_format} content: {exc}") from exc

    if not records:
        raise SequenceIOError(f"No sequence records were found in the {resolved_format} input.")

    return records
