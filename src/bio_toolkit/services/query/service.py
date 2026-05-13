from __future__ import annotations

import re
from typing import Any

from bio_toolkit.contracts.query.models import (
    AlphaFoldPayload,
    FetchPreview,
    ProviderSearchPayload,
)
from bio_toolkit.contracts.search.models import SearchHit
from bio_toolkit.providers.alphafold.client import AlphaFoldError, fetch_alphafold_prediction
from bio_toolkit.providers.kegg.client import (
    KeggError,
    fetch_kegg_entry,
    fetch_kegg_sequence,
    is_kegg_identifier,
    search_kegg,
    summarize_kegg_entry,
)
from bio_toolkit.providers.ncbi.client import NcbiClient, NcbiError
from bio_toolkit.providers.selection import (
    infer_query_provider,
    normalize_kegg_search_database,
    normalize_query_provider,
)
from bio_toolkit.providers.uniprot.client import (
    UniProtError,
    fetch_uniprot_entry,
    is_uniprot_accession,
    search_uniprot,
    summarize_uniprot_entry,
)

from .errors import QueryServiceError
from .request import QueryRequest
from .response import QueryResponse


def run_query(request: QueryRequest, *, settings: Any) -> QueryResponse:
    clean_query = request.query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty.")

    resolved_provider = normalize_query_provider(request.provider)
    if resolved_provider == "auto":
        resolved_provider = infer_query_provider(clean_query)

    if resolved_provider == "alphafold":
        return _build_alphafold_report(clean_query)
    if resolved_provider == "uniprot":
        return _build_uniprot_report(
            query=clean_query,
            organism=request.organism,
            limit=request.limit,
        )
    if resolved_provider == "kegg":
        return _build_kegg_report(
            query=clean_query,
            database=request.database,
            limit=request.limit,
        )
    if settings is None:
        raise QueryServiceError("Settings are required for NCBI queries.")
    return _build_ncbi_report(
        settings=settings,
        query=clean_query,
        database=request.database,
        organism=request.organism,
        limit=request.limit,
        rettype=request.rettype,
    )


def _build_ncbi_report(
    *,
    settings: Any,
    query: str,
    database: str,
    organism: str,
    limit: int,
    rettype: str,
) -> QueryResponse:
    resolved_database = database.strip().lower()
    if resolved_database in {"", "auto"}:
        resolved_database = "nucleotide"

    client = NcbiClient.from_settings(settings)
    results = client.search(
        database=resolved_database,
        query=query,
        organism=organism,
        limit=limit,
    )

    fetch_preview = None
    fetch_accession = _candidate_ncbi_accession(query, results)
    if fetch_accession is not None:
        try:
            fetched = client.fetch(
                database=resolved_database,
                accession=fetch_accession,
                rettype=rettype,
            )
        except (NcbiError, ValueError):
            fetched = None
        if fetched is not None:
            fetch_preview = FetchPreview(
                accession=fetched.accession,
                database=fetched.database,
                rettype=fetched.rettype,
                preview=_preview_text(fetched.content, 8),
            )

    return QueryResponse(
        provider="ncbi",
        kind="search",
        query=query,
        result_count=len(results),
        payload=ProviderSearchPayload(
            database=resolved_database,
            organism=organism,
            results=[_provider_result_to_hit(item) for item in results],
            fetch_preview=fetch_preview,
        ),
    )


def _build_uniprot_report(
    *,
    query: str,
    organism: str,
    limit: int,
) -> QueryResponse:
    if is_uniprot_accession(query):
        entry = fetch_uniprot_entry(query)
        accession = str(entry.get("primaryAccession") or query)
        return QueryResponse(
            provider="uniprot",
            kind="entry",
            query=query,
            result_count=1,
            payload=ProviderSearchPayload(
                organism=organism,
                results=[],
                entry=summarize_uniprot_entry(entry),
                alphafold=_safe_alphafold(accession),
            ),
        )

    results = search_uniprot(query=query, organism=organism, limit=limit)
    top_hit = _uniprot_top_hit(results)
    top_hit_entry = None
    top_hit_alphafold = None
    if top_hit is not None:
        try:
            entry = fetch_uniprot_entry(top_hit.accession)
        except UniProtError:
            entry = None
        if entry is not None:
            top_hit_entry = summarize_uniprot_entry(entry)
            top_hit_alphafold = _safe_alphafold(top_hit.accession)

    return QueryResponse(
        provider="uniprot",
        kind="search",
        query=query,
        result_count=len(results),
        payload=ProviderSearchPayload(
            organism=organism,
            results=[_provider_result_to_hit(item) for item in results],
            top_hit_entry=top_hit_entry,
            alphafold=top_hit_alphafold,
        ),
    )


def _build_kegg_report(
    *,
    query: str,
    database: str,
    limit: int,
) -> QueryResponse:
    resolved_database = database.strip().lower()
    if resolved_database in {"", "auto"}:
        resolved_database = "genes"
    resolved_database = normalize_kegg_search_database(resolved_database)

    if is_kegg_identifier(query):
        payload = fetch_kegg_entry(query)
        return QueryResponse(
            provider="kegg",
            kind="entry",
            query=query,
            result_count=1,
            payload=ProviderSearchPayload(
                database=resolved_database,
                results=[],
                entry=summarize_kegg_entry(query, payload),
                sequence_preview=_safe_kegg_sequence(query),
            ),
        )

    results = search_kegg(query=query, database=resolved_database, limit=limit)
    top_hit = results[0] if len(results) == 1 else None
    top_hit_entry = None
    top_hit_sequence = None
    if top_hit is not None:
        try:
            payload = fetch_kegg_entry(top_hit.accession)
        except KeggError:
            payload = None
        if payload is not None:
            top_hit_entry = summarize_kegg_entry(top_hit.accession, payload)
            top_hit_sequence = _safe_kegg_sequence(top_hit.accession)

    return QueryResponse(
        provider="kegg",
        kind="search",
        query=query,
        result_count=len(results),
        payload=ProviderSearchPayload(
            database=resolved_database,
            results=[_provider_result_to_hit(item) for item in results],
            top_hit_entry=top_hit_entry,
            sequence_preview=top_hit_sequence,
        ),
    )


def _build_alphafold_report(query: str) -> QueryResponse:
    if not is_uniprot_accession(query):
        raise QueryServiceError(
            f"AlphaFold requires a UniProt accession ID (e.g. P38398, Q9Y6K9), "
            f"not a search term. Got: {query!r}"
        )
    prediction = fetch_alphafold_prediction(query)
    return QueryResponse(
        provider="alphafold",
        kind="entry",
        query=query,
        result_count=0 if prediction is None else 1,
        payload=AlphaFoldPayload(prediction=prediction),
    )


def _candidate_ncbi_accession(query: str, results: list[Any]) -> str | None:
    clean_query = query.strip()
    for item in results:
        accession = str(getattr(item, "accession", "")).strip()
        if accession.upper() == clean_query.upper():
            return accession

    if _looks_like_ncbi_accession(clean_query):
        return clean_query
    return None


def _looks_like_ncbi_accession(value: str) -> bool:
    if " " in value or len(value) < 4:
        return False
    upper_value = value.upper()
    if "_" in upper_value or "." in upper_value:
        return bool(re.fullmatch(r"^[A-Z]{1,6}_?\d+(?:\.\d+)?$", upper_value))
    return bool(re.fullmatch(r"^[A-Z]{1,4}\d{5,}(?:\.\d+)?$", upper_value))


def _preview_text(content: str, preview_lines: int) -> str:
    return "\n".join(content.splitlines()[:preview_lines]).strip()


def _safe_alphafold(accession: str) -> dict[str, Any] | None:
    try:
        return fetch_alphafold_prediction(accession)
    except AlphaFoldError:
        return None


def _safe_kegg_sequence(accession: str) -> dict[str, Any] | None:
    try:
        fetched = fetch_kegg_sequence(accession)
    except KeggError:
        return None

    sequence_lines = [line.strip() for line in fetched.content.splitlines() if line.strip()]
    sequence = "".join(line for line in sequence_lines[1:] if not line.startswith(">"))
    return {
        "database": fetched.database,
        "length": len(sequence) or None,
        "preview": sequence[:80] + ("..." if len(sequence) > 80 else ""),
    }


def _uniprot_top_hit(results: list[Any]) -> Any | None:
    if len(results) == 1:
        return results[0]
    return None


def _provider_result_to_hit(item: Any) -> SearchHit:
    length = getattr(item, "length", None)
    return SearchHit(
        accession=str(getattr(item, "accession", "")),
        title=str(getattr(item, "title", "")),
        organism=_normalize_optional_text(getattr(item, "organism", None)),
        length=None if length in (None, "") else int(length),
    )


def _normalize_optional_text(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
