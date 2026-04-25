from bio_toolkit.contracts.annotate.models import AnnotatedRecord
from bio_toolkit.contracts.common.models import SourceRef
from bio_toolkit.domain.annotations import build_annotation_report

from .helpers import load_annotation_input
from .request import AnnotateRequest
from .response import AnnotateResponse


def run_annotation(request: AnnotateRequest, *, settings) -> AnnotateResponse:
    records, resolved_format, source_info = load_annotation_input(request, settings=settings)
    report = build_annotation_report(
        records=records,
        input_format=resolved_format,
        source_info=source_info,
        feature_limit=request.feature_limit,
    )
    return AnnotateResponse(
        source=SourceRef(**source_info),
        input_format=resolved_format,
        record_count=report["record_count"],
        feature_limit=request.feature_limit,
        records=[AnnotatedRecord.model_validate(record) for record in report["records"]],
    )
