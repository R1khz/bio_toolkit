import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
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
        response = SimpleNamespace(
            provider="uniprot",
            kind="entry",
            query="P69905",
            result_count=1,
            model_dump=lambda: {
                "provider": "uniprot",
                "kind": "entry",
                "query": "P69905",
                "entry": {"accession": "P69905"},
            },
        )

        with patch("bio_toolkit.cli.commands.query.run_query", return_value=response):
            result = self.runner.invoke(
                app,
                ["query", "P69905", "--provider", "uniprot", "--json"],
            )

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        self.assertIn('"provider": "uniprot"', result.stdout)
        self.assertIn('"accession": "P69905"', result.stdout)

    def test_query_command_renders_terminal_report(self) -> None:
        response = SimpleNamespace(
            provider="alphafold",
            kind="entry",
            query="P69905",
            result_count=1,
            payload=SimpleNamespace(prediction={"model_id": "AF-P69905-F1"}),
        )

        with patch("bio_toolkit.cli.commands.query.run_query", return_value=response):
            with patch("bio_toolkit.cli.commands.query.render_query_response") as render_report:
                result = self.runner.invoke(
                    app,
                    ["query", "P69905", "--provider", "alphafold"],
                )

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        render_report.assert_called_once()


if __name__ == "__main__":
    unittest.main()
