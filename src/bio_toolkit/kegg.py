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


def fetch_kegg_entry(
    accession: str,
    *,
    timeout_seconds: float = 20.0,
) -> str:
    clean_accession = accession.strip()
    if not clean_accession:
        raise ValueError("KEGG accession cannot be empty.")

    return _request_text(
        f"{KEGG_API_BASE_URL}/get/{quote(clean_accession)}",
        timeout_seconds=timeout_seconds,
    )


def summarize_kegg_entry(accession: str, payload: str) -> dict[str, object]:
    fields = _parse_kegg_fields(payload)
    pathways = _named_entry_rows(fields.get("PATHWAY", []))
    diseases = _named_entry_rows(fields.get("DISEASE", []))
    dblinks = _database_links(fields.get("DBLINKS", []))
    motifs = _flat_values(fields.get("MOTIF", []))
    orthology = _named_entry_rows(fields.get("ORTHOLOGY", []))
    brite = _flat_values(fields.get("BRITE", []))
    network = _named_entry_rows(fields.get("NETWORK", []))
    aa_sequence = _sequence_block(fields.get("AASEQ", []))
    nt_sequence = _sequence_block(fields.get("NTSEQ", []))

    return {
        "accession": accession,
        "entry": _entry_token(fields.get("ENTRY", []), accession),
        "name": _first_value(fields.get("NAME", []), accession),
        "definition": _first_value(fields.get("DEFINITION", []), ""),
        "organism": _organism_from_fields(fields),
        "position": _first_value(fields.get("POSITION", []), ""),
        "pathways": pathways,
        "diseases": diseases,
        "orthology": orthology,
        "network": network,
        "brite": brite[:12],
        "motifs": motifs[:12],
        "database_links": dblinks,
        "aa_sequence_length": aa_sequence["length"],
        "aa_sequence_preview": aa_sequence["preview"],
        "nt_sequence_length": nt_sequence["length"],
        "nt_sequence_preview": nt_sequence["preview"],
        "has_amino_acid_sequence": aa_sequence["length"] is not None,
        "has_nucleotide_sequence": nt_sequence["length"] is not None,
    }


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


def _parse_kegg_fields(payload: str) -> dict[str, list[str]]:
    fields: dict[str, list[str]] = {}
    current_key = ""
    for line in payload.splitlines():
        key = line[:12].strip()
        value = line[12:].strip()
        if key:
            current_key = key
            fields.setdefault(key, []).append(value)
            continue
        if current_key:
            fields.setdefault(current_key, []).append(value)
    return fields


def _first_value(values: list[str], default: str) -> str:
    for value in values:
        cleaned = value.strip()
        if cleaned:
            return cleaned
    return default


def _entry_token(values: list[str], default: str) -> str:
    value = _first_value(values, default)
    return value.split()[0] if value else default


def _named_entry_rows(values: list[str]) -> list[dict[str, str]]:
    rows = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        if " " in cleaned:
            identifier, text = cleaned.split(None, 1)
        else:
            identifier, text = cleaned, ""
        rows.append({"id": identifier.strip(), "text": text.strip()})
    return rows[:20]


def _database_links(values: list[str]) -> list[dict[str, str]]:
    rows = []
    for value in values:
        cleaned = value.strip()
        if not cleaned:
            continue
        if ":" in cleaned:
            database, identifiers = cleaned.split(":", maxsplit=1)
        else:
            database, identifiers = cleaned, ""
        rows.append(
            {
                "database": database.strip(),
                "ids": identifiers.strip(),
            }
        )
    return rows[:20]


def _flat_values(values: list[str]) -> list[str]:
    return [value.strip() for value in values if value.strip()]


def _organism_from_fields(fields: dict[str, list[str]]) -> str:
    organism_values = fields.get("ORGANISM", [])
    if not organism_values:
        return ""
    first_value = organism_values[0].strip()
    if " " in first_value:
        _, description = first_value.split(None, 1)
        return description.strip()
    return first_value


def _sequence_block(values: list[str]) -> dict[str, int | str | None]:
    if not values:
        return {"length": None, "preview": ""}

    length = None
    sequence_parts = []
    for index, value in enumerate(values):
        cleaned = value.replace(" ", "").strip()
        if not cleaned:
            continue
        if index == 0 and cleaned.isdigit():
            length = int(cleaned)
            continue
        sequence_parts.append(cleaned)

    sequence = "".join(sequence_parts)
    if length is None and sequence:
        length = len(sequence)

    preview = sequence[:80] + ("..." if len(sequence) > 80 else "") if sequence else ""
    return {"length": length, "preview": preview}
