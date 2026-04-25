from __future__ import annotations

from io import StringIO

from Bio import SeqIO
from Bio.SeqRecord import SeqRecord

from .sequence_reader import SequenceIOError


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
