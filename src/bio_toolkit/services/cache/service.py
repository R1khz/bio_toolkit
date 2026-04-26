from __future__ import annotations

from bio_toolkit.config import refresh_settings
from bio_toolkit.storage.cache import CacheStore

from .errors import CacheServiceError
from .request import CacheRequest
from .response import CacheResponse


def run_cache(request: CacheRequest) -> CacheResponse:
    settings = refresh_settings()
    store = CacheStore(settings.cache_dir)

    if request.accession is None:
        records = store.list_records(database=request.database, rettype=request.rettype)
        return CacheResponse(records=[_to_cached_record(item) for item in records])

    lookup_database = request.database or "nucleotide"
    lookup_rettype = request.rettype or "fasta"
    loaded = store.load_fetch_result(
        accession=request.accession,
        database=lookup_database,
        rettype=lookup_rettype,
    )
    if loaded is None:
        raise CacheServiceError(
            "No cached record matched that accession/database/rettype combination."
        )

    cache_record, fetch_result = loaded
    return CacheResponse(
        record=_to_cached_record(cache_record),
        preview="\n".join(fetch_result.content.splitlines()[: request.preview_lines]),
    )


def _to_cached_record(record) -> dict:
    return {
        "accession": record.accession,
        "database": record.database,
        "rettype": record.rettype,
        "source": record.source,
        "fetched_at": record.fetched_at,
        "content_path": record.content_path,
        "file_size": record.file_size,
    }
