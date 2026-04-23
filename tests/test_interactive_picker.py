import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from rich.console import Console

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cli import _run_interactive_search_flow  # noqa: E402
from bio_toolkit.interactive_picker import (  # noqa: E402
    format_search_choice,
    pick_post_search_action,
)
from bio_toolkit.ncbi import FetchResult, SearchResult  # noqa: E402


class FakePrompt:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    def ask(self) -> str:
        return self.answer


class FakeQuestionary:
    class Choice:
        def __init__(self, title: str, value) -> None:
            self.title = title
            self.value = value

    class Separator:
        pass

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.choices = []

    def select(self, _message: str, *, choices, instruction: str, use_indicator: bool):
        self.choices = choices
        return FakePrompt(self.answer)


class InteractivePickerTests(unittest.TestCase):
    def test_pick_post_search_action_offers_analyze_now(self) -> None:
        result = SearchResult(
            accession="NP_123456.1",
            title="Example sporulation protein",
            organism="Bacillus subtilis",
            source_db="refseq",
            uid="1",
            length=742,
        )
        fake_questionary = FakeQuestionary(answer="analyze")

        with patch(
            "bio_toolkit.interactive_picker._load_questionary",
            return_value=fake_questionary,
        ):
            with patch("bio_toolkit.interactive_picker._ensure_tty"):
                action = pick_post_search_action(result)

        choice_titles = [
            choice.title for choice in fake_questionary.choices if hasattr(choice, "title")
        ]

        self.assertEqual(action, "analyze")
        self.assertIn("Analyze now", choice_titles)
        self.assertIn("Query API details", choice_titles)

    def test_format_search_choice_is_readable(self) -> None:
        result = SearchResult(
            accession="NP_123456.1",
            title="Example sporulation protein",
            organism="Bacillus subtilis",
            source_db="refseq",
            uid="1",
            length=742,
        )

        rendered = format_search_choice(result)

        self.assertIn("NP_123456.1", rendered)
        self.assertIn("Bacillus subtilis", rendered)
        self.assertIn("742", rendered)
        self.assertIn("Example sporulation protein", rendered)

    def test_interactive_search_flow_can_analyze_without_rendering_fetch_preview(self) -> None:
        result = SearchResult(
            accession="NP_123456.1",
            title="Example sporulation protein",
            organism="Bacillus subtilis",
            source_db="refseq",
            uid="1",
            length=742,
        )
        fetched = FetchResult(
            accession="NP_123456.1",
            database="protein",
            rettype="fasta",
            content=">NP_123456.1\nMKWVTFISLLLLFSSAYSR\n",
            file_suffix=".fasta",
            source="cache",
        )
        console = Console(record=True)

        with patch("bio_toolkit.cli.pick_search_result", return_value=result):
            with patch("bio_toolkit.cli.pick_post_search_action", return_value="analyze"):
                with patch("bio_toolkit.cli.ensure_runtime_dirs"):
                    with patch(
                        "bio_toolkit.cli._resolve_fetch",
                        return_value=(None, None, fetched),
                    ):
                        with patch("bio_toolkit.cli._render_fetch_output") as render_fetch:
                            with patch("bio_toolkit.cli._analyze_fetched_record") as analyze:
                                _run_interactive_search_flow(
                                    console=console,
                                    settings=object(),
                                    database="protein",
                                    results=[result],
                                )

        render_fetch.assert_not_called()
        analyze.assert_called_once_with(console=console, record=fetched, min_orf_aa=30)

    def test_interactive_search_flow_can_render_query_details(self) -> None:
        result = SearchResult(
            accession="P69905",
            title="Hemoglobin subunit alpha",
            organism="Homo sapiens",
            source_db="uniprotkb",
            uid="P69905",
            provider="uniprot",
            database="protein",
        )
        console = Console(record=True)
        report = {"provider": "uniprot", "kind": "entry", "query": "P69905"}

        with patch("bio_toolkit.cli.pick_search_result", return_value=result):
            with patch("bio_toolkit.cli.pick_post_search_action", return_value="query_details"):
                with patch(
                    "bio_toolkit.cli.build_provider_query_report",
                    return_value=report,
                ) as build_report:
                    with patch(
                        "bio_toolkit.cli._render_provider_query_report"
                    ) as render_report:
                        _run_interactive_search_flow(
                            console=console,
                            settings=object(),
                            database="protein",
                            results=[result],
                        )

        build_report.assert_called_once()
        render_report.assert_called_once_with(console=console, report=report)


if __name__ == "__main__":
    unittest.main()
