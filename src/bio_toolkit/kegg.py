from __future__ import annotations

from urllib.parse import quote
from urllib.request import Request, urlopen

from bio_toolkit.ncbi import FetchResult, SearchResult, validate_limit

KEGG_API_BASE_URL = "https://rest.kegg.jp"
SUPPORTED_KEGG_DATABASES = {"genes", "pathway", "ko", "enzyme", "disease"}


class KeggError(RuntimeError):
    """Raised when a KEGG request or response fails."""


class KeggNotFoundError(KeggError):
    """Raised when a KEGG endpoint returns 404."""


def search_kegg(
    *,
    query: str,
    database: str = "genes",
    limit: int = 10,
    timeout_seconds: float = 20.0,
) -> list[SearchResult]:
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty.")

    resolved_limit = validate_limit(limit)
    resolved_database = normalize_kegg_database(database)
    if is_kegg_identifier(clean_query):
        return [
            _kegg_identifier_result(
                clean_query,
                fallback_database=resolved_database,
                timeout_seconds=timeout_seconds,
            )
        ]

    payload = _request_text(
        f"{KEGG_API_BASE_URL}/find/{resolved_database}/{quote(clean_query)}",
        timeout_seconds=timeout_seconds,
    )

    results = []
    for line in payload.splitlines():
        if not line.strip():
            continue
        try:
            accession, title = line.split("\t", maxsplit=1)
        except ValueError:
            accession = line.strip()
            title = "-"
        organism = accession.split(":", maxsplit=1)[0] if ":" in accession else "-"
        results.append(
            SearchResult(
                accession=accession.strip(),
                title=title.strip(),
                organism=organism,
                source_db=f"kegg:{resolved_database}",
                uid=accession.strip(),
                provider="kegg",
                database=resolved_database,
            )
        )
        if len(results) >= resolved_limit:
            break

    return results


def fetch_kegg_sequence(
    accession: str,
    *,
    timeout_seconds: float = 20.0,
) -> FetchResult:
    clean_accession = accession.strip()
    if not clean_accession:
        raise ValueError("KEGG accession cannot be empty.")

    last_error: Exception | None = None
    for sequence_mode in ("aaseq", "ntseq"):
        try:
            content = _request_text(
                f"{KEGG_API_BASE_URL}/get/{quote(clean_accession)}/{sequence_mode}",
                timeout_seconds=timeout_seconds,
            )
        except KeggNotFoundError as exc:
            last_error = exc
            continue

        if content.strip():
            database = "protein" if sequence_mode == "aaseq" else "nucleotide"
            return FetchResult(
                accession=clean_accession,
                database=database,
                rettype="fasta",
                content=content,
                file_suffix=".fasta",
                source="kegg",
                provider="kegg",
            )

    raise KeggError(
        f"KEGG did not return a protein or nucleotide sequence for {clean_accession}."
    ) from last_error


def normalize_kegg_database(database: str) -> str:
    resolved = database.strip().lower()
    if resolved not in SUPPORTED_KEGG_DATABASES:
        allowed = ", ".join(sorted(SUPPORTED_KEGG_DATABASES))
        raise ValueError(f"Unsupported KEGG database '{database}'. Use one of: {allowed}.")
    return resolved


def is_kegg_identifier(value: str) -> bool:
    clean_value = value.strip()
    if ":" not in clean_value:
        return False
    prefix, suffix = clean_value.split(":", maxsplit=1)
    return prefix.isalnum() and suffix.strip() != ""


def _kegg_identifier_result(
    accession: str,
    *,
    fallback_database: str,
    timeout_seconds: float,
) -> SearchResult:
    payload = _request_text(
        f"{KEGG_API_BASE_URL}/get/{quote(accession)}",
        timeout_seconds=timeout_seconds,
    )
    database = _database_from_identifier(accession, fallback_database)
    return SearchResult(
        accession=accession,
        title=_entry_field(payload, "DEFINITION") or _entry_field(payload, "NAME") or accession,
        organism=_entry_organism(payload) or accession.split(":", maxsplit=1)[0],
        source_db=f"kegg:{database}",
        uid=accession,
        provider="kegg",
        database=database,
    )


def _database_from_identifier(accession: str, fallback_database: str) -> str:
    prefix = accession.split(":", maxsplit=1)[0].lower()
    if prefix in SUPPORTED_KEGG_DATABASES:
        return prefix
    return "genes" if prefix.isalpha() and len(prefix) <= 4 else fallback_database


def _entry_field(payload: str, field_name: str) -> str:
    prefix = f"{field_name:<12}"
    collecting = False
    parts: list[str] = []

    for line in payload.splitlines():
        if line.startswith(prefix):
            collecting = True
            parts.append(line[12:].strip())
            continue
        if collecting and line.startswith(" " * 12):
            parts.append(line[12:].strip())
            continue
        if collecting:
            break

    return " ".join(part for part in parts if part).strip()


def _entry_organism(payload: str) -> str:
    organism_line = _entry_field(payload, "ORGANISM")
    if not organism_line:
        return ""
    if "  " in organism_line:
        return organism_line.split("  ", maxsplit=1)[1].strip()
    return organism_line


def _request_text(url: str, *, timeout_seconds: float) -> str:
    request = Request(
        url,
        headers={"User-Agent": "bio-toolkit/0.1", "Accept": "text/plain"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        message = str(exc)
        if "HTTP Error 404" in message:
            raise KeggNotFoundError(f"KEGG resource was not found for {url}.") from exc
        raise KeggError(f"KEGG request failed for {url}: {exc}") from exc
