import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cli import app  # noqa: E402


class QueryCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_query_command_emits_json(self) -> None:
        report = {
            "provider": "uniprot",
            "kind": "entry",
            "query": "P69905",
            "entry": {"accession": "P69905"},
        }

        with patch("bio_toolkit.cli.build_provider_query_report", return_value=report):
            result = self.runner.invoke(
                app,
                ["query", "P69905", "--provider", "uniprot", "--json"],
            )

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        self.assertIn('"provider": "uniprot"', result.stdout)
        self.assertIn('"accession": "P69905"', result.stdout)

    def test_query_command_renders_terminal_report(self) -> None:
        report = {
            "provider": "alphafold",
            "kind": "entry",
            "query": "P69905",
            "result_count": 1,
            "prediction": {"model_id": "AF-P69905-F1"},
        }

        with patch("bio_toolkit.cli.build_provider_query_report", return_value=report):
            with patch("bio_toolkit.cli._render_provider_query_report") as render_report:
                result = self.runner.invoke(
                    app,
                    ["query", "P69905", "--provider", "alphafold"],
                )

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        render_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
