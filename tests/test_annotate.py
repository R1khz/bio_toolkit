import sys
import tempfile
import unittest
from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, SeqFeature
from Bio.SeqRecord import SeqRecord
from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cli import app  # noqa: E402


class AnnotateCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_annotate_genbank_file_and_export_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            gb_path = tmp_path / "sample.gb"
            export_path = tmp_path / "sample.md"

            record = SeqRecord(
                Seq("ATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG"),
                id="gb1",
                name="gb1",
                description="Example GenBank record",
            )
            record.annotations["molecule_type"] = "DNA"
            record.annotations["organism"] = "Bacillus subtilis"
            record.annotations["source"] = "Bacillus subtilis"
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
                    },
                ),
            ]
            SeqIO.write([record], gb_path, "genbank")

            result = self.runner.invoke(
                app,
                [
                    "annotate",
                    str(gb_path),
                    "--output",
                    str(export_path),
                    "--export-format",
                    "markdown",
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Annotation Report", result.stdout)
            self.assertIn("Annotation Summary", result.stdout)
            self.assertTrue(export_path.exists())
            exported = export_path.read_text(encoding="utf-8")
            self.assertIn("# Annotation Report", exported)
            self.assertIn("gb1", exported)
            self.assertIn("spoIIIAA", exported)


if __name__ == "__main__":
    unittest.main()
