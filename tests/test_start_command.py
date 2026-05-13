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
from bio_toolkit.ncbi import NcbiError  # noqa: E402


def _guided_search_input() -> dict[str, str | int]:
    return {
        "mode": "search",
        "query": "BRCA1",
        "provider": "ncbi",
        "database": "nucleotide",
        "organism": "",
        "limit": 10,
    }


def _search_start_response() -> SimpleNamespace:
    return SimpleNamespace(
        kind="search",
        payload={
            "provider": "ncbi",
            "database_label": "NCBI:nucleotide",
            "result_count": 1,
            "results": [
                {
                    "accession": "NM_000001.1",
                    "title": "Example transcript",
                    "organism": "Homo sapiens",
                    "length": 100,
                }
            ],
        },
    )


def _query_guided_search_input() -> dict[str, str | int]:
    return {
        "mode": "query",
        "query": "insulin",
        "provider": "auto",
        "database": "nucleotide",
        "organism": "human",
        "limit": 100,
    }


def _query_start_response() -> SimpleNamespace:
    return SimpleNamespace(
        kind="query",
        payload={
            "provider": "ncbi",
            "kind": "search",
            "query": "insulin",
            "result_count": 1,
            "results": [
                {
                    "accession": "NM_001284847.2",
                    "title": "insulin transcript variant",
                    "organism": "Homo sapiens",
                    "length": 3007,
                }
            ],
            "database": "nucleotide",
            "organism": "human",
            "fetch_preview": None,
        },
    )


class StartCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()
        self.network_error = NcbiError(
            "NCBI request failed for https://eutils.ncbi.nlm.nih.gov/...: "
            "<urlopen error [Errno -2] Name or service not known>"
        )

    def test_start_reports_actionable_guidance_for_remote_search_failures(self) -> None:
        with patch(
            "bio_toolkit.cli.commands.start.prompt_guided_search",
            return_value=_guided_search_input(),
        ):
            with patch(
                "bio_toolkit.cli.commands.start.refresh_settings",
                return_value=SimpleNamespace(),
            ):
                with patch(
                    "bio_toolkit.cli.commands.start.run_start",
                    side_effect=self.network_error,
                ):
                    result = self.runner.invoke(app, ["start"])

        self.assertEqual(result.exit_code, 1, msg=result.stdout)
        self.assertIn("NCBI request failed", result.stdout)
        self.assertIn("Check internet/DNS connectivity", result.stdout)

    def test_start_handles_interactive_follow_up_failures_without_crashing(self) -> None:
        with patch(
            "bio_toolkit.cli.commands.start.prompt_guided_search",
            return_value=_guided_search_input(),
        ):
            with patch(
                "bio_toolkit.cli.commands.start.refresh_settings",
                return_value=SimpleNamespace(),
            ):
                with patch(
                    "bio_toolkit.cli.commands.start.run_start",
                    return_value=_search_start_response(),
                ):
                    with patch("bio_toolkit.cli.commands.start.render_search_response"):
                        with patch(
                            "bio_toolkit.cli.commands.start.run_interactive_search_flow",
                            side_effect=self.network_error,
                        ):
                            result = self.runner.invoke(app, ["start"])

        self.assertEqual(result.exit_code, 1, msg=result.stdout)
        self.assertIn("NCBI request failed", result.stdout)
        self.assertIn("Check internet/DNS connectivity", result.stdout)

    def test_start_query_mode_renders_flattened_query_payload(self) -> None:
        with patch(
            "bio_toolkit.cli.commands.start.prompt_guided_search",
            return_value=_query_guided_search_input(),
        ):
            with patch(
                "bio_toolkit.cli.commands.start.refresh_settings",
                return_value=SimpleNamespace(),
            ):
                with patch(
                    "bio_toolkit.cli.commands.start.run_start",
                    return_value=_query_start_response(),
                ):
                    with patch(
                        "bio_toolkit.cli.commands.start.render_query_response"
                    ) as render_query_response:
                        result = self.runner.invoke(app, ["start"])

        self.assertEqual(result.exit_code, 0, msg=result.stdout)
        render_query_response.assert_called_once()


if __name__ == "__main__":
    unittest.main()
