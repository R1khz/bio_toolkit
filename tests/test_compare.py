import json
import sys
import tempfile
from pathlib import Path
import unittest

from typer.testing import CliRunner


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cli import app  # noqa: E402


class CompareCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_compare_local_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta_a = tmp_path / "seq_a.fasta"
            fasta_b = tmp_path / "seq_b.fasta"
            report = tmp_path / "compare-report.json"

            fasta_a.write_text(">seqA\nATGCGTATGCGTGAATTC\n", encoding="utf-8")
            fasta_b.write_text(">seqB\nATGGCCATTGTAATGGGCCGCTGAAAGGGTGCCCGATAG\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                [
                    "compare",
                    str(fasta_a),
                    str(fasta_b),
                    "--output",
                    str(report),
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Comparison Report", result.stdout)
            self.assertIn("Compared Records", result.stdout)
            self.assertTrue(report.exists())

            payload = json.loads(report.read_text(encoding="utf-8"))
            self.assertEqual(payload["target_count"], 2)
            self.assertEqual(payload["record_count"], 2)
            self.assertTrue(payload["comparison"]["all_same_molecule_type"])
            self.assertEqual(payload["comparison"]["molecule_types"], ["DNA"])


if __name__ == "__main__":
    unittest.main()
