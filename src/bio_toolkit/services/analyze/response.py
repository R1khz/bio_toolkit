from bio_toolkit.contracts.analyze.models import AnalyzedRecord
from bio_toolkit.contracts.common.models import ContractModel, SourceRef


class AnalyzeResponse(ContractModel):
    source: SourceRef
    input_format: str
    record_count: int
    records: list[AnalyzedRecord]
