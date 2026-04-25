from typing import Any

from bio_toolkit.contracts.search.models import SearchHit
from bio_toolkit.providers.kegg.client import search_kegg
from bio_toolkit.providers.ncbi.client import NcbiClient
from bio_toolkit.providers.selection import (
    infer_search_provider,
    normalize_kegg_search_database,
    normalize_search_provider,
)
from bio_toolkit.providers.uniprot.client import search_uniprot

from .errors import SearchServiceError
from .request import SearchRequest
from .response import SearchResponse


def run_search(request: SearchRequest, *, settings: Any) -> SearchResponse:
    resolved_provider = normalize_search_provider(request.provider)
    if resolved_provider == "auto":
        resolved_provider = infer_search_provider(request.query)

    if resolved_provider == "ncbi":
        if settings is None:
            raise SearchServiceError("Settings are required for NCBI searches.")
        results = NcbiClient.from_settings(settings).search(
            database=request.database,
            query=request.query,
            organism=request.organism,
            limit=request.limit,
        )
        return SearchResponse(
            provider="ncbi",
            database_label=f"NCBI:{request.database}",
            result_count=len(results),
            results=[_provider_result_to_hit(item) for item in results],
        )

    if resolved_provider == "uniprot":
        results = search_uniprot(
            query=request.query,
            organism=request.organism,
            limit=request.limit,
        )
        return SearchResponse(
            provider="uniprot",
            database_label="UniProt",
            result_count=len(results),
            results=[_provider_result_to_hit(item) for item in results],
        )

    kegg_database = _resolve_kegg_database(request.database)
    results = search_kegg(query=request.query, database=kegg_database, limit=request.limit)
    return SearchResponse(
        provider="kegg",
        database_label=f"KEGG:{kegg_database}",
        result_count=len(results),
        results=[_provider_result_to_hit(item) for item in results],
    )


def _resolve_kegg_database(database: str) -> str:
    try:
        return normalize_kegg_search_database(database)
    except ValueError:
        return "genes"


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
