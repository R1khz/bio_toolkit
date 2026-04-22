import sys
import unittest
from pathlib import Path

from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, SeqFeature
from Bio.SeqRecord import SeqRecord

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.annotations import build_annotation_report  # noqa: E402


class AnnotationTests(unittest.TestCase):
    def test_builds_annotation_report_from_genbank_like_record(self) -> None:
        record = SeqRecord(
            Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"),
            id="gb1",
            name="gb1",
            description="Example GenBank record",
        )
        record.annotations["molecule_type"] = "DNA"
        record.annotations["organism"] = "Bacillus subtilis"
        record.annotations["source"] = "Bacillus subtilis"
        record.annotations["keywords"] = ["sporulation", "example"]
        record.annotations["taxonomy"] = ["Bacteria", "Firmicutes", "Bacilli"]
        record.annotations["accessions"] = ["ABC123"]
        record.annotations["topology"] = "linear"
        record.annotations["date"] = "19-APR-2026"
        record.features = [
            SeqFeature(FeatureLocation(0, 39), type="source"),
            SeqFeature(FeatureLocation(0, 39), type="gene", qualifiers={"gene": ["spoIIIAA"]}),
            SeqFeature(
                FeatureLocation(0, 39),
                type="CDS",
                qualifiers={
                    "gene": ["spoIIIAA"],
                    "product": ["stage III sporulation protein AA"],
                    "locus_tag": ["BSU00010"],
                    "protein_id": ["XP_000001"],
                },
            ),
        ]

        report = build_annotation_report(
            records=[record],
            input_format="genbank",
            source_info={"kind": "file", "label": "/tmp/example.gb"},
            feature_limit=5,
        )

        self.assertEqual(report["record_count"], 1)
        annotated = report["records"][0]
        self.assertEqual(annotated["accession"], "ABC123")
        self.assertEqual(annotated["organism"], "Bacillus subtilis")
        self.assertIn("spoIIIAA", annotated["gene_names"])
        self.assertIn("stage III sporulation protein AA", annotated["product_names"])
        self.assertEqual(annotated["feature_counts"]["gene"], 1)
        self.assertEqual(annotated["feature_counts"]["CDS"], 1)
        self.assertGreaterEqual(len(annotated["selected_features"]), 1)


if __name__ == "__main__":
    unittest.main()
