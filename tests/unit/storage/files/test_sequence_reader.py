from pathlib import Path

from bio_toolkit.storage.files.sequence_reader import detect_input_format


def test_detect_input_format_from_suffix() -> None:
    assert detect_input_format(path=Path("example.fasta")) == "fasta"
