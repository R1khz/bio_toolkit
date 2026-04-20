import sys
from pathlib import Path
import unittest

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.analysis import SequenceAnalyzer, compare_sequence_records, detect_molecule_type  # noqa: E402


class AnalysisTests(unittest.TestCase):
    def test_detects_dna_record(self) -> None:
        record = SeqRecord(Seq("ATGCGTATTAACCGG"), id="dna1")
        self.assertEqual(detect_molecule_type(record), "DNA")

    def test_analyzes_nucleotide_record(self) -> None:
        record = SeqRecord(
            Seq("GCCACCATGGAACTGAAATAGGAATTC"),
            id="dna1",
            description="DNA example",
        )
        result = SequenceAnalyzer(min_orf_aa=2).analyze_record(record)

        self.assertEqual(result["molecule_type"], "DNA")
        self.assertEqual(result["analysis"]["basic_stats"]["length"], len(record.seq))
        self.assertGreater(result["analysis"]["basic_stats"]["gc_content"], 0)
        self.assertGreaterEqual(result["analysis"]["orfs"]["orfs_found"], 1)
        self.assertEqual(result["analysis"]["motifs"]["restriction_sites"][0]["enzyme"], "EcoRI")

    def test_analyzes_protein_record(self) -> None:
        record = SeqRecord(Seq("MKWVTFISLLLLFSSAYSR"), id="prot1", description="Protein example")
        result = SequenceAnalyzer().analyze_record(record)

        self.assertEqual(result["molecule_type"], "PROTEIN")
        self.assertIn("molecular_weight", result["analysis"]["basic_stats"])
        self.assertTrue(result["analysis"]["motifs"]["skipped"])
        self.assertTrue(result["analysis"]["orfs"]["skipped"])

    def test_compares_analyzed_records(self) -> None:
        analyzer = SequenceAnalyzer(min_orf_aa=2)
        dna_a = analyzer.analyze_record(
            SeqRecord(Seq("GCCACCATGGAACTGAAATAGGAATTC"), id="dna1", description="DNA one")
        )
        dna_b = analyzer.analyze_record(
            SeqRecord(Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"), id="dna2", description="DNA two")
        )

        comparison = compare_sequence_records([dna_a, dna_b])

        self.assertEqual(comparison["record_count"], 2)
        self.assertTrue(comparison["all_same_molecule_type"])
        self.assertEqual(comparison["molecule_types"], ["DNA"])
        self.assertGreaterEqual(comparison["length"]["delta"], 1)
        self.assertIsNotNone(comparison["nucleotide"])
        self.assertIsNone(comparison["protein"])


if __name__ == "__main__":
    unittest.main()
