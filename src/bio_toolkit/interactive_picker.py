from __future__ import annotations

import sys

from bio_toolkit.ncbi import SearchResult


class InteractivePickerError(RuntimeError):
    """Raised when terminal selection cannot run."""


class InteractivePickerCancelled(RuntimeError):
    """Raised when the user cancels an interactive selection."""


def pick_search_result(results: list[SearchResult]) -> SearchResult:
    questionary = _load_questionary()
    _ensure_tty()

    choices = [
        questionary.Choice(title=format_search_choice(result), value=result) for result in results
    ]
    choices.append(questionary.Separator())
    choices.append(questionary.Choice(title="Cancel", value=None))

    answer = questionary.select(
        "Select a search result",
        choices=choices,
        instruction="Use arrows to move, Enter to confirm",
        use_indicator=True,
    ).ask()

    if answer is None:
        raise InteractivePickerCancelled("Interactive selection cancelled.")
    return answer


def pick_post_search_action(result: SearchResult) -> str:
    questionary = _load_questionary()
    _ensure_tty()

    answer = questionary.select(
        f"What do you want to do with {result.accession}?",
        choices=[
            questionary.Choice("Fetch and save", value="fetch"),
            questionary.Choice("Fetch, save, and analyze", value="fetch_analyze"),
            questionary.Choice("Print accession only", value="print_accession"),
            questionary.Separator(),
            questionary.Choice("Cancel", value=None),
        ],
        instruction="Use arrows to move, Enter to confirm",
        use_indicator=True,
    ).ask()

    if answer is None:
        raise InteractivePickerCancelled("Interactive action selection cancelled.")
    return answer


def format_search_choice(result: SearchResult) -> str:
    organism = result.organism or "-"
    length = f"{result.length:,}" if isinstance(result.length, int) else "-"
    return f"{result.accession} | {organism} | {result.source_db} | {length} | {result.title}"


def _ensure_tty() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise InteractivePickerError(
            "Interactive selection requires a TTY-capable terminal session."
        )


def _load_questionary():
    try:
        import questionary
    except ImportError as exc:  # pragma: no cover - dependency/runtime issue
        raise InteractivePickerError(
            "Interactive selection requires the `questionary` dependency."
        ) from exc

    return questionary
