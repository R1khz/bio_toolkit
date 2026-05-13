import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.interactive_picker import (  # noqa: E402
    InteractivePickerCancelled,
    InteractivePickerError,
    format_search_choice,
    pick_post_search_action,
    pick_search_result,
    prompt_guided_search,
)
from bio_toolkit.ncbi import SearchResult  # noqa: E402


class FakePrompt:
    def __init__(self, answer: str) -> None:
        self.answer = answer

    def ask(self) -> str:
        return self.answer


class FakeQuestionary:
    class Choice:
        def __init__(self, title: str, value) -> None:
            self.title = title
            self.value = title if value is None else value

    class Separator:
        pass

    def __init__(self, answer: str) -> None:
        self.answer = answer
        self.choices = []

    def select(self, _message: str, *, choices, instruction: str, use_indicator: bool):
        self.choices = choices
        return FakePrompt(self.answer)


class GuidedFakeQuestionary:
    class Choice:
        def __init__(self, title: str, value) -> None:
            self.title = title
            self.value = title if value is None else value

    class Separator:
        pass

    def __init__(self, *, select_answers: list[str], text_answers: list[str]) -> None:
        self._select_answers = iter(select_answers)
        self._text_answers = iter(text_answers)
        self.text_calls: list[tuple[str, str]] = []

    def select(self, _message: str, *, choices, instruction: str, use_indicator: bool):
        del choices, instruction, use_indicator
        return FakePrompt(next(self._select_answers))

    def text(self, message: str, default: str = ""):
        self.text_calls.append((message, default))
        return FakePrompt(next(self._text_answers))


class CancelChoiceQuestionary:
    class Choice:
        def __init__(self, title: str, value) -> None:
            self.title = title
            self.value = title if value is None else value

    class Separator:
        pass

    def select(self, _message: str, *, choices, instruction: str, use_indicator: bool):
        del instruction, use_indicator
        choice = next(item for item in reversed(choices) if hasattr(item, "value"))
        return FakePrompt(choice.value)


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

    def test_pick_search_result_cancel_raises_cancelled(self) -> None:
        result = SearchResult(
            accession="NP_123456.1",
            title="Example sporulation protein",
            organism="Bacillus subtilis",
            source_db="refseq",
            uid="1",
            length=742,
        )

        with patch(
            "bio_toolkit.interactive_picker._load_questionary",
            return_value=CancelChoiceQuestionary(),
        ):
            with patch("bio_toolkit.interactive_picker._ensure_tty"):
                with self.assertRaises(InteractivePickerCancelled):
                    pick_search_result([result])

    def test_pick_post_search_action_cancel_raises_cancelled(self) -> None:
        result = SearchResult(
            accession="NP_123456.1",
            title="Example sporulation protein",
            organism="Bacillus subtilis",
            source_db="refseq",
            uid="1",
            length=742,
        )

        with patch(
            "bio_toolkit.interactive_picker._load_questionary",
            return_value=CancelChoiceQuestionary(),
        ):
            with patch("bio_toolkit.interactive_picker._ensure_tty"):
                with self.assertRaises(InteractivePickerCancelled):
                    pick_post_search_action(result)

    def test_prompt_guided_search_cancel_raises_cancelled(self) -> None:
        with patch(
            "bio_toolkit.interactive_picker._load_questionary",
            return_value=CancelChoiceQuestionary(),
        ):
            with patch("bio_toolkit.interactive_picker._ensure_tty"):
                with self.assertRaises(InteractivePickerCancelled):
                    prompt_guided_search()

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

    def test_prompt_guided_search_uses_blank_limit_prompt_and_defaults_to_ten(self) -> None:
        fake_questionary = GuidedFakeQuestionary(
            select_answers=["search", "auto"],
            text_answers=["BRCA1", "", ""],
        )

        with patch(
            "bio_toolkit.interactive_picker._load_questionary",
            return_value=fake_questionary,
        ):
            with patch("bio_toolkit.interactive_picker._ensure_tty"):
                result = prompt_guided_search()

        self.assertEqual(result["limit"], 10)
        self.assertIn(("How many results? [default: 10]", ""), fake_questionary.text_calls)

    def test_prompt_guided_search_rejects_non_numeric_limits(self) -> None:
        fake_questionary = GuidedFakeQuestionary(
            select_answers=["search", "auto"],
            text_answers=["BRCA1", "", "abc"],
        )

        with patch(
            "bio_toolkit.interactive_picker._load_questionary",
            return_value=fake_questionary,
        ):
            with patch("bio_toolkit.interactive_picker._ensure_tty"):
                with self.assertRaises(InteractivePickerError):
                    prompt_guided_search()


if __name__ == "__main__":
    unittest.main()
