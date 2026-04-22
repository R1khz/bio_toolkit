import sys
import tempfile
import unittest
from pathlib import Path

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cli import app  # noqa: E402


class AnalyzeCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_analyze_local_file_supports_custom_motif_output(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta = tmp_path / "seq.fasta"
            fasta.write_text(">seq1\nGCCACCATGGAACTGAAATAGGAATTC\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                [
                    "analyze",
                    str(fasta),
                    "--min-orf-aa",
                    "2",
                    "--motif",
                    "GAATTC",
                    "--motif",
                    "re:GCCACCATG",
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Custom Motifs", result.stdout)
            self.assertIn("GAATTC", result.stdout)
            self.assertIn("Longest ORF Translation", result.stdout)
            self.assertIn("Longest ORF Codon", result.stdout)
            self.assertIn("Usage", result.stdout)

    def test_analyze_local_file_exports_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta = tmp_path / "seq.fasta"
            report = tmp_path / "analysis.csv"
            fasta.write_text(">seq1\nGCCACCATGGAACTGAAATAGGAATTC\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                [
                    "analyze",
                    str(fasta),
                    "--output",
                    str(report),
                    "--export-format",
                    "csv",
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Analysis Report", result.stdout)
            self.assertIn("CSV report written to:", result.stdout)
            self.assertTrue(report.exists())
            exported = report.read_text(encoding="utf-8")
            self.assertIn("source_kind,source_label,input_format,sequence_id", exported)
            self.assertIn("seq1", exported)


if __name__ == "__main__":
    unittest.main()
