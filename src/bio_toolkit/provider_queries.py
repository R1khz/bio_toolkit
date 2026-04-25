from typing import Any

from bio_toolkit.services.query.request import QueryRequest
from bio_toolkit.services.query.service import run_query


def build_provider_query_report(
    *,
    settings,
    provider: str,
    query: str,
    database: str = "auto",
    organism: str = "",
    limit: int = 5,
    rettype: str = "fasta",
) -> dict[str, Any]:
    request = QueryRequest(
        query=query,
        provider=provider,
        database=database,
        organism=organism,
        limit=limit,
        rettype=rettype,
    )
    return run_query(request, settings=settings).model_dump()
