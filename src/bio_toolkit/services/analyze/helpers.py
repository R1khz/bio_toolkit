from __future__ import annotations

from pathlib import Path
from typing import Any

from bio_toolkit.storage.cache import CacheError, CacheStore
from bio_toolkit.storage.files import (
    SequenceIOError,
    format_from_rettype,
    load_records_from_path,
    load_records_from_text,
)

from .errors import AnalyzeServiceError
from .request import AnalyzeRequest


def load_analysis_input(
    request: AnalyzeRequest,
    *,
    settings: Any,
) -> tuple[list, str, dict[str, str]]:
    normalized_source = request.source.strip().lower()
    if normalized_source not in {"auto", "file", "cache"}:
        raise ValueError("Unsupported source. Use one of: auto, file, cache.")

    target_path = Path(request.target)
    if normalized_source in {"auto", "file"} and target_path.exists():
        records, resolved_format = load_records_from_path(
            target_path, input_format=request.input_format
        )
        return (
            records,
            resolved_format,
            {"kind": "file", "label": str(target_path.resolve())},
        )

    if normalized_source == "file":
        raise SequenceIOError(f"Local input file was not found: {request.target}")

    if settings is None:
        raise AnalyzeServiceError("Settings are required for cache-backed analysis input.")

    cache_store = CacheStore(settings.cache_dir)

    if request.database or request.rettype:
        lookup_database = request.database or "nucleotide"
        lookup_rettype = request.rettype or "fasta"
        loaded = cache_store.load_fetch_result(
            accession=request.target,
            database=lookup_database,
            rettype=lookup_rettype,
        )
        if loaded is None:
            raise CacheError(
                "No cached record matched that accession/database/rettype combination."
            )
        cache_record, fetch_result = loaded
    else:
        matches = cache_store.find_records_by_accession(request.target)
        if not matches:
            raise CacheError(
                "No cached record matched that accession. Provide --database/--rettype "
                "or fetch it first."
            )
        if len(matches) > 1:
            raise CacheError(
                "Multiple cached records matched that accession. Re-run with --database "
                "and --rettype."
            )
        cache_record = matches[0]
        loaded = cache_store.load_fetch_result(
            accession=cache_record.accession,
            database=cache_record.database,
            rettype=cache_record.rettype,
        )
        if loaded is None:
            raise CacheError("Cached record metadata exists but the record could not be loaded.")
        _, fetch_result = loaded

    resolved_input_format = (
        format_from_rettype(cache_record.rettype)
        if request.input_format == "auto"
        else request.input_format
    )
    records, resolved_format = load_records_from_text(
        fetch_result.content,
        input_format=resolved_input_format,
    )
    return (
        records,
        resolved_format,
        {
            "kind": "cache",
            "label": cache_record.accession,
            "accession": cache_record.accession,
            "database": cache_record.database,
            "provider": fetch_result.provider,
            "rettype": cache_record.rettype,
        },
    )
