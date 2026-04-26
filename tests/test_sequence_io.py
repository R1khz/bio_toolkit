import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.sequence_io import (  # noqa: E402
    detect_input_format,
    dump_records_to_text,
    format_from_rettype,
    load_records_from_path,
    load_records_from_text,
)


class SequenceIOTests(unittest.TestCase):
    def test_loads_fasta_from_text(self) -> None:
        records, resolved_format = load_records_from_text(">seq1\nATGCATGC\n", input_format="auto")

        self.assertEqual(resolved_format, "fasta")
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0].id, "seq1")

    def test_loads_genbank_from_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.gb"
            record = SeqRecord(Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"), id="gb1", name="gb1")
            record.annotations["molecule_type"] = "DNA"
            SeqIO.write([record], path, "genbank")

            records, resolved_format = load_records_from_path(path, input_format="auto")

            self.assertEqual(resolved_format, "genbank")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].id, "gb1")

    def test_loads_fasta_from_unknown_suffix_without_path_read_text(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "sample.txt"
            path.write_text(">seq1\nATGCATGC\n", encoding="utf-8")

            with patch.object(
                Path,
                "read_text",
                side_effect=AssertionError("unexpected read_text"),
            ):
                records, resolved_format = load_records_from_path(path, input_format="auto")

            self.assertEqual(resolved_format, "fasta")
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].id, "seq1")

    def test_relative_format_helpers(self) -> None:
        self.assertEqual(detect_input_format(input_format="gb", text="LOCUS test"), "genbank")
        self.assertEqual(format_from_rettype("gb"), "genbank")
        self.assertEqual(format_from_rettype("fasta"), "fasta")

    def test_dumps_records_to_fasta_text(self) -> None:
        record = SeqRecord(Seq("ATGC"), id="seq1", description="Example")
        dumped = dump_records_to_text([record], output_format="fasta")

        self.assertIn(">seq1 Example", dumped)
        self.assertIn("ATGC", dumped)


if __name__ == "__main__":
    unittest.main()
