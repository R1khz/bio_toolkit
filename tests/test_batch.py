import json
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


class BatchCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_batch_analyze_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta_a = tmp_path / "seq_a.fasta"
            fasta_b = tmp_path / "seq_b.fasta"
            targets = tmp_path / "targets.txt"
            report = tmp_path / "batch-report.json"

            fasta_a.write_text(">seqA\nATGCGTATGCGT\n", encoding="utf-8")
            fasta_b.write_text(">seqB\nMKWVTFISLLLLFSSAYSR\n", encoding="utf-8")
            targets.write_text("seq_a.fasta\nseq_b.fasta\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                [
                    "batch",
                    str(targets),
                    "--mode",
                    "analyze",
                    "--input-kind",
                    "files",
                    "--output",
                    str(report),
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Batch Summary", result.stdout)
            self.assertIn("Succeeded", result.stdout)
            self.assertTrue(report.exists())

            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["mode"], "analyze")
            self.assertEqual(payload["succeeded"], 2)
            self.assertEqual(payload["failed"], 0)
            self.assertEqual(payload["results"][0]["status"], "ok")
            self.assertEqual(payload["results"][1]["status"], "ok")

    def test_batch_analyze_local_files_exports_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta = tmp_path / "seq_a.fasta"
            targets = tmp_path / "targets.txt"
            report = tmp_path / "batch-report.csv"

            fasta.write_text(">seqA\nATGCGTATGCGTGAATTC\n", encoding="utf-8")
            targets.write_text("seq_a.fasta\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                [
                    "batch",
                    str(targets),
                    "--mode",
                    "analyze",
                    "--input-kind",
                    "files",
                    "--output",
                    str(report),
                    "--export-format",
                    "csv",
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Batch Summary", result.stdout)
            self.assertIn("CSV batch report written to:", result.stdout)
            self.assertTrue(report.exists())
            exported = report.read_text(encoding="utf-8")
            self.assertIn("item,operation,status,source_kind,source_label", exported)
            self.assertIn("seqA", exported)


if __name__ == "__main__":
    unittest.main()
