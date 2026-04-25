from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

from bio_toolkit.storage.files.sequence_reader import (
    _read_text_prefix,
    detect_input_format,
    load_records_from_text,
)
from bio_toolkit.storage.files.sequence_writer import dump_records_to_text


def test_detect_input_format_from_suffix() -> None:
    assert detect_input_format(path=Path("example.fasta")) == "fasta"


def test_detect_input_format_from_unknown_suffix_with_long_leading_whitespace(
    tmp_path: Path,
) -> None:
    path = tmp_path / "example.txt"
    path.write_text((" " * 5000) + ">seq1\nATGC\n", encoding="utf-8")

    resolved_format = detect_input_format(
        path=path,
        text=_read_text_prefix(path),
        input_format="auto",
    )

    assert resolved_format == "fasta"


def test_storage_file_modules_can_parse_and_serialize_fasta_text() -> None:
    records, resolved_format = load_records_from_text(">seq1\nATGC\n", input_format="auto")
    dumped = dump_records_to_text(
        [SeqRecord(Seq("ATGC"), id="seq2", description="Example")],
        output_format="fasta",
    )

    assert resolved_format == "fasta"
    assert records[0].id == "seq1"
    assert ">seq2 Example" in dumped
