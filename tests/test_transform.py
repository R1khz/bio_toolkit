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


class TransformCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_transform_reverse_complement_local_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta = tmp_path / "seq.fasta"
            output = tmp_path / "seq.revcomp.fasta"
            fasta.write_text(">seq1\nATGC\n", encoding="utf-8")

            result = self.runner.invoke(
                app,
                [
                    "transform",
                    str(fasta),
                    "--operation",
                    "reverse-complement",
                    "--output",
                    str(output),
                ],
            )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Transform Output", result.stdout)
            self.assertTrue(output.exists())
            self.assertIn("GCAT", output.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
