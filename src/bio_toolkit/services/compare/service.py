from bio_toolkit.domain.analysis import SequenceAnalyzer, compare_sequence_records
from bio_toolkit.services.analyze.helpers import load_analysis_input
from bio_toolkit.services.analyze.request import AnalyzeRequest

from .request import CompareRequest
from .response import CompareResponse


def run_compare(request: CompareRequest, *, settings) -> CompareResponse:
    compared_records = []
    target_summaries = []

    for target in request.targets:
        records, resolved_format, source_info = load_analysis_input(
            AnalyzeRequest(
                target=target,
                source=request.source,
                input_format=request.input_format,
                database=request.database,
                rettype=request.rettype,
            ),
            settings=settings,
        )
        analyzed_records = SequenceAnalyzer(min_orf_aa=request.min_orf_aa).analyze_records(records)

        for analyzed_record in analyzed_records:
            compared_records.append(analyzed_record | {"source": source_info})

        target_summaries.append(
            {
                "target": target,
                "source": source_info,
                "input_format": resolved_format,
                "record_count": len(analyzed_records),
            }
        )

    return CompareResponse(
        target_count=len(request.targets),
        record_count=len(compared_records),
        targets=target_summaries,
        records=compared_records,
        comparison=compare_sequence_records(compared_records),
    )
