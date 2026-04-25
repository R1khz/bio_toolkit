from bio_toolkit.domain.sequences import transform_records
from bio_toolkit.services.analyze.helpers import load_analysis_input
from bio_toolkit.services.analyze.request import AnalyzeRequest
from bio_toolkit.storage.files import dump_records_to_text

from .request import TransformRequest
from .response import TransformResponse


def run_transform(request: TransformRequest, *, settings) -> TransformResponse:
    records, resolved_format, source_info = load_analysis_input(
        AnalyzeRequest(
            target=request.target,
            source=request.source,
            input_format=request.input_format,
            database=request.database,
            rettype=request.rettype,
        ),
        settings=settings,
    )
    transformed_records, transform_meta = transform_records(
        records=records,
        operation=request.operation,
        frame=request.frame,
        to_stop=request.to_stop,
        start=request.start,
        end=None if request.end == 0 else request.end,
    )
    fasta_text = dump_records_to_text(transformed_records, output_format="fasta")
    return TransformResponse(
        source=source_info,
        input_format=resolved_format,
        operation=transform_meta["operation"],
        parameters=transform_meta,
        input_record_count=len(records),
        output_record_count=len(transformed_records),
        output_format="fasta",
        target=request.target,
        fasta_text=fasta_text,
    )
