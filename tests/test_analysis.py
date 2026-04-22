import sys
import unittest
from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqRecord import SeqRecord

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.analysis import (  # noqa: E402
    SequenceAnalyzer,
    compare_sequence_records,
    detect_molecule_type,
)


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

    def test_analyzes_nucleotide_record_with_custom_motifs_and_orf_translation(self) -> None:
        record = SeqRecord(
            Seq("GCCACCATGGAACTGAAATAGGAATTC"),
            id="dna1",
            description="DNA example",
        )
        result = SequenceAnalyzer(
            min_orf_aa=2,
            custom_motifs=["GAATTC", "re:GCCACCATG"],
        ).analyze_record(record)

        self.assertEqual(result["analysis"]["basic_stats"]["ambiguous_count"], 0)
        self.assertEqual(len(result["analysis"]["custom_motifs"]), 2)
        self.assertEqual(result["analysis"]["custom_motifs"][0]["count"], 1)
        self.assertEqual(result["analysis"]["custom_motifs"][1]["match_type"], "regex")
        self.assertEqual(result["analysis"]["orfs"]["longest_orf"]["protein_sequence"], "MELK")
        self.assertEqual(result["analysis"]["orfs"]["longest_orf"]["codon_usage"]["ATG"], 1)
        self.assertTrue(
            any("short" in warning.lower() for warning in result["analysis"]["warnings"])
        )

    def test_analyzes_protein_record(self) -> None:
        record = SeqRecord(
            Seq("MAAAAAGKTLLLLLLLLLLLLFSSAYSR"),
            id="prot1",
            description="Protein example",
        )
        result = SequenceAnalyzer().analyze_record(record)

        self.assertEqual(result["molecule_type"], "PROTEIN")
        self.assertIn("molecular_weight", result["analysis"]["basic_stats"])
        self.assertTrue(result["analysis"]["motifs"]["skipped"])
        self.assertTrue(result["analysis"]["orfs"]["skipped"])
        self.assertGreaterEqual(result["analysis"]["domains"]["domains_found"], 1)

    def test_analyzes_protein_record_with_warnings(self) -> None:
        record = SeqRecord(Seq("MXXWV*"), id="prot2", description="Protein warning example")
        result = SequenceAnalyzer().analyze_record(record)

        joined_warnings = " ".join(result["analysis"]["warnings"]).lower()

        self.assertIn("ambiguous residues", joined_warnings)
        self.assertIn("stop symbols", joined_warnings)

    def test_analyzes_uniprot_style_header_candidates_without_crashing(self) -> None:
        record = SeqRecord(
            Seq("MKWVTFISLLLLFSSAYSR"),
            id="sp|P69905|HBA_HUMAN",
            description="sp|P69905|HBA_HUMAN Hemoglobin subunit alpha",
        )

        result = SequenceAnalyzer().analyze_record(record)

        self.assertEqual(result["molecule_type"], "PROTEIN")
        self.assertIn("domains", result["analysis"])

    def test_compares_analyzed_records(self) -> None:
        analyzer = SequenceAnalyzer(min_orf_aa=2)
        dna_a = analyzer.analyze_record(
            SeqRecord(Seq("GCCACCATGGAACTGAAATAGGAATTC"), id="dna1", description="DNA one")
        )
        dna_b = analyzer.analyze_record(
            SeqRecord(
                Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"), id="dna2", description="DNA two"
            )
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
