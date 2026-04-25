from __future__ import annotations

from typing import Any

from bio_toolkit.contracts.fetch.models import FetchedRecord
from bio_toolkit.providers.ncbi.client import NcbiClient
from bio_toolkit.storage.cache.store import CacheStore

from .errors import FetchServiceError
from .request import FetchRequest
from .response import FetchResponse


def run_fetch(
    request: FetchRequest,
    *,
    settings: Any,
    cache_store: CacheStore | None = None,
    ncbi_client: NcbiClient | None = None,
) -> FetchResponse:
    store = cache_store or _build_cache_store(settings)

    if request.use_cache and not request.refresh:
        cached = store.load_fetch_result(
            accession=request.accession,
            database=request.database,
            rettype=request.rettype,
        )
        if cached is not None:
            cache_record, record = cached
            return FetchResponse(
                accession=request.accession,
                cache_hit=True,
                record=_to_fetched_record(record),
                cache_path=str(store.resolve_content_path(cache_record)),
            )

    client = ncbi_client or _build_ncbi_client(settings)
    fetched = client.fetch(
        database=request.database,
        accession=request.accession,
        rettype=request.rettype,
    )
    saved = store.save_fetch_result(fetched) if request.save_cache else None
    return FetchResponse(
        accession=request.accession,
        cache_hit=False,
        record=_to_fetched_record(fetched),
        cache_path=None if saved is None else str(store.resolve_content_path(saved)),
    )


def _build_cache_store(settings: Any) -> CacheStore:
    if settings is None:
        raise FetchServiceError("Settings are required when no cache store is provided.")
    return CacheStore(settings.cache_dir)


def _build_ncbi_client(settings: Any) -> NcbiClient:
    if settings is None:
        raise FetchServiceError("Settings are required when no NCBI client is provided.")
    return NcbiClient.from_settings(settings)


def _to_fetched_record(record: Any) -> FetchedRecord:
    return FetchedRecord(
        accession=str(record.accession),
        database=str(record.database),
        rettype=str(record.rettype),
        source=str(record.source),
        content=str(record.content),
    )
