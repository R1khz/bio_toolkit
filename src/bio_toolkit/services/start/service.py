from __future__ import annotations

from bio_toolkit.contracts.analyze.models import AnalyzedRecord
from bio_toolkit.contracts.common.models import SourceRef
from bio_toolkit.providers.selection import infer_query_input
from bio_toolkit.services.analyze.response import AnalyzeResponse
from bio_toolkit.services.query import QueryRequest, run_query
from bio_toolkit.services.search import SearchRequest, run_search
from bio_toolkit.storage.files import load_records_from_text

from ...domain.analysis.sequence_analyzer import SequenceAnalyzer
from ..analyze.service import _enrich_protein_analysis_records
from .request import StartRequest
from .response import StartResponse


def run_start(request: StartRequest, *, settings) -> StartResponse:
    query_info = infer_query_input(request.query)
    if request.mode == "search" and query_info["kind"] == "sequence":
        response = _build_guided_sequence_response(query_info)
        return StartResponse(kind="analysis", payload=response.model_dump())

    if request.mode == "query":
        response = run_query(
            QueryRequest(
                query=request.query,
                provider=request.provider,
                database=request.database,
                organism=request.organism,
                limit=request.limit,
                rettype="fasta",
            ),
            settings=settings,
        )
        return StartResponse(kind="query", payload=response.model_dump())

    response = run_search(
        SearchRequest(
            query=request.query,
            provider=request.provider,
            database=request.database,
            organism=request.organism,
            limit=request.limit,
        ),
        settings=settings,
    )
    return StartResponse(kind="search", payload=response.model_dump())


def _build_guided_sequence_response(query_info: dict[str, str]) -> AnalyzeResponse:
    sequence_text = f">guided_query\n{query_info['normalized']}\n"
    records, resolved_format = load_records_from_text(sequence_text, input_format="fasta")
    analyzed_records = SequenceAnalyzer(min_orf_aa=30).analyze_records(records)
    source_info = {
        "kind": "guided-sequence",
        "label": "guided-query",
        "provider": "local-sequence",
    }
    _enrich_protein_analysis_records(analyzed_records, source_info)
    return AnalyzeResponse(
        source=SourceRef(**source_info),
        input_format=resolved_format,
        record_count=len(analyzed_records),
        records=[AnalyzedRecord.model_validate(record) for record in analyzed_records],
    )
