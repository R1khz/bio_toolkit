import sys
from pathlib import Path
import unittest

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.transforms import (  # noqa: E402
    TransformError,
    normalize_transform_name,
    transform_records,
)


class TransformTests(unittest.TestCase):
    def test_normalizes_transform_name(self) -> None:
        self.assertEqual(normalize_transform_name("revcomp"), "reverse-complement")
        self.assertEqual(normalize_transform_name("translate"), "translate")

    def test_reverse_complement_transform(self) -> None:
        record = SeqRecord(Seq("ATGC"), id="dna1", description="DNA example")
        transformed, meta = transform_records(records=[record], operation="reverse-complement")

        self.assertEqual(meta["operation"], "reverse-complement")
        self.assertEqual(len(transformed), 1)
        self.assertEqual(str(transformed[0].seq), "GCAT")

    def test_translate_transform(self) -> None:
        record = SeqRecord(Seq("ATGGCC"), id="dna1", description="DNA example")
        transformed, meta = transform_records(records=[record], operation="translate", frame=1)

        self.assertEqual(meta["operation"], "translate")
        self.assertEqual(str(transformed[0].seq), "MA")

    def test_subsequence_transform(self) -> None:
        record = SeqRecord(Seq("ATGGCC"), id="dna1", description="DNA example")
        transformed, meta = transform_records(records=[record], operation="subseq", start=2, end=5)

        self.assertEqual(meta["operation"], "subseq")
        self.assertEqual(str(transformed[0].seq), "TGGC")

    def test_invalid_reverse_complement_on_protein(self) -> None:
        record = SeqRecord(Seq("MKWVTF"), id="prot1", description="Protein example")
        with self.assertRaises(TransformError):
            transform_records(records=[record], operation="reverse-complement")


if __name__ == "__main__":
    unittest.main()
