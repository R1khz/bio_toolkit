from __future__ import annotations

import os
import sys

from bio_toolkit.ncbi import SearchResult

_CANCEL_SELECTION = object()


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
    choices.append(questionary.Choice(title="Cancel", value=_CANCEL_SELECTION))

    answer = questionary.select(
        "Select a search result",
        choices=choices,
        instruction="Use arrows to move, Enter to confirm",
        use_indicator=True,
    ).ask()

    if answer is None or answer is _CANCEL_SELECTION:
        raise InteractivePickerCancelled("Interactive selection cancelled.")
    return answer


def pick_post_search_action(result: SearchResult) -> str:
    questionary = _load_questionary()
    _ensure_tty()

    provider = getattr(result, "provider", "ncbi").strip().lower()
    if provider == "uniprot":
        choices = [
            questionary.Choice("Fetch and save", value="fetch"),
            questionary.Choice("Analyze now", value="analyze"),
            questionary.Choice("Query API details", value="query_details"),
            questionary.Choice("BLAST now", value="blast"),
            questionary.Choice("Show AlphaFold model", value="alphafold"),
            questionary.Choice("Fetch, save, and analyze", value="fetch_analyze"),
            questionary.Choice("Print accession only", value="print_accession"),
            questionary.Separator(),
            questionary.Choice("Cancel", value=_CANCEL_SELECTION),
        ]
    elif provider == "kegg":
        kegg_database = getattr(result, "database", "genes").strip().lower()
        if kegg_database == "genes":
            choices = [
                questionary.Choice("Fetch and save", value="fetch"),
                questionary.Choice("Analyze now", value="analyze"),
                questionary.Choice("Query API details", value="query_details"),
                questionary.Choice("BLAST now", value="blast"),
                questionary.Choice("Fetch, save, and analyze", value="fetch_analyze"),
                questionary.Choice("Print accession only", value="print_accession"),
                questionary.Separator(),
                questionary.Choice("Cancel", value=_CANCEL_SELECTION),
            ]
        else:
            choices = [
                questionary.Choice("Query API details", value="query_details"),
                questionary.Choice("Print accession only", value="print_accession"),
                questionary.Separator(),
                questionary.Choice("Cancel", value=_CANCEL_SELECTION),
            ]
    else:
        choices = [
            questionary.Choice("Fetch and save", value="fetch"),
            questionary.Choice("Analyze now", value="analyze"),
            questionary.Choice("Query API details", value="query_details"),
            questionary.Choice("Annotate now", value="annotate"),
            questionary.Choice("BLAST now", value="blast"),
            questionary.Choice("Fetch, save, and analyze", value="fetch_analyze"),
            questionary.Choice("Print accession only", value="print_accession"),
            questionary.Separator(),
            questionary.Choice("Cancel", value=_CANCEL_SELECTION),
        ]

    answer = questionary.select(
        f"What do you want to do with {result.accession}?",
        choices=choices,
        instruction="Use arrows to move, Enter to confirm",
        use_indicator=True,
    ).ask()

    if answer is None or answer is _CANCEL_SELECTION:
        raise InteractivePickerCancelled("Interactive action selection cancelled.")
    return answer


def format_search_choice(result: SearchResult) -> str:
    organism = result.organism or "-"
    length = f"{result.length:,}" if isinstance(result.length, int) else "-"
    return f"{result.accession} | {organism} | {result.source_db} | {length} | {result.title}"


def prompt_guided_search() -> dict[str, str | int]:
    questionary = _load_questionary()
    _ensure_tty()

    mode = questionary.select(
        "What do you want to do?",
        choices=[
            questionary.Choice("Search records", value="search"),
            questionary.Choice("Query API details", value="query"),
            questionary.Separator(),
            questionary.Choice("Cancel", value=_CANCEL_SELECTION),
        ],
        instruction="Use arrows to move, Enter to confirm",
        use_indicator=True,
    ).ask()
    if mode is None or mode is _CANCEL_SELECTION:
        raise InteractivePickerCancelled("Guided search cancelled.")

    query = questionary.text("What do you want to search for?").ask()
    if query is None or not str(query).strip():
        raise InteractivePickerCancelled("Guided search cancelled.")

    provider_choices = [
        questionary.Choice("Auto", value="auto"),
        questionary.Choice("NCBI", value="ncbi"),
        questionary.Choice("UniProt", value="uniprot"),
        questionary.Choice("KEGG", value="kegg"),
    ]
    if str(mode) == "query":
        provider_choices.append(questionary.Choice("AlphaFold", value="alphafold"))
    provider_choices.extend(
        [
            questionary.Separator(),
            questionary.Choice("Cancel", value=_CANCEL_SELECTION),
        ]
    )
    provider = questionary.select(
        (
            "Where do you want to search?"
            if str(mode) == "search"
            else "Which API do you want to query?"
        ),
        choices=provider_choices,
        instruction="Use arrows to move, Enter to confirm",
        use_indicator=True,
    ).ask()
    if provider is None or provider is _CANCEL_SELECTION:
        raise InteractivePickerCancelled("Guided search cancelled.")

    limit = 1 if str(provider) == "alphafold" else 10
    if str(provider) == "ncbi":
        database = questionary.select(
            "Which NCBI database?",
            choices=[
                questionary.Choice("Nucleotide", value="nucleotide"),
                questionary.Choice("Protein", value="protein"),
                questionary.Separator(),
                questionary.Choice("Cancel", value=_CANCEL_SELECTION),
            ],
            instruction="Use arrows to move, Enter to confirm",
            use_indicator=True,
        ).ask()
        if database is None or database is _CANCEL_SELECTION:
            raise InteractivePickerCancelled("Guided search cancelled.")
        organism = questionary.text("Organism filter (optional)", default="").ask()
        if organism is None:
            raise InteractivePickerCancelled("Guided search cancelled.")
    elif str(provider) == "kegg":
        database = questionary.select(
            "Which KEGG database?",
            choices=[
                questionary.Choice("Genes", value="genes"),
                questionary.Choice("Pathway", value="pathway"),
                questionary.Choice("KO", value="ko"),
                questionary.Choice("Enzyme", value="enzyme"),
                questionary.Choice("Disease", value="disease"),
                questionary.Separator(),
                questionary.Choice("Cancel", value=_CANCEL_SELECTION),
            ],
            instruction="Use arrows to move, Enter to confirm",
            use_indicator=True,
        ).ask()
        if database is None or database is _CANCEL_SELECTION:
            raise InteractivePickerCancelled("Guided search cancelled.")
        organism = ""
    elif str(provider) == "uniprot":
        database = "protein"
        organism = questionary.text("Organism filter (optional)", default="").ask()
        if organism is None:
            raise InteractivePickerCancelled("Guided search cancelled.")
    elif str(provider) == "alphafold":
        database = "protein"
        organism = ""
    else:
        database = "nucleotide"
        organism = questionary.text("Organism filter (optional)", default="").ask()
        if organism is None:
            raise InteractivePickerCancelled("Guided search cancelled.")

    if str(provider) != "alphafold":
        limit_text = questionary.text("How many results? [default: 10]", default="").ask()
        if limit_text is None:
            raise InteractivePickerCancelled("Guided search cancelled.")

        limit = _parse_guided_search_limit(limit_text, default_limit=10)

    return {
        "mode": str(mode),
        "query": str(query).strip(),
        "provider": str(provider),
        "database": str(database),
        "organism": str(organism).strip(),
        "limit": limit,
    }


def _ensure_tty() -> None:
    if not sys.stdin.isatty() or not sys.stdout.isatty():
        raise InteractivePickerError(
            "Interactive selection requires a TTY-capable terminal session."
        )


def _parse_guided_search_limit(limit_text: str, *, default_limit: int) -> int:
    clean_limit = str(limit_text).strip()
    if not clean_limit:
        return default_limit

    try:
        return int(clean_limit)
    except ValueError as exc:
        raise InteractivePickerError("Guided search limit must be a whole number.") from exc


def _load_questionary():
    os.environ.setdefault("PROMPT_TOOLKIT_NO_CPR", "1")
    try:
        import questionary
    except ImportError as exc:  # pragma: no cover - dependency/runtime issue
        raise InteractivePickerError(
            "Interactive selection requires the `questionary` dependency."
        ) from exc

    return questionary
