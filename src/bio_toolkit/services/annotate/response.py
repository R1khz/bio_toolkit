from bio_toolkit.contracts.annotate.models import AnnotatedRecord
from bio_toolkit.contracts.common.models import ContractModel, SourceRef


class AnnotateResponse(ContractModel):
    source: SourceRef
    input_format: str
    record_count: int
    feature_limit: int
    records: list[AnnotatedRecord]
