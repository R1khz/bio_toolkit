from typing import Any

from bio_toolkit.contracts.common.models import ContractModel, SourceRef


class TransformResponse(ContractModel):
    source: SourceRef
    input_format: str
    operation: str
    parameters: dict[str, Any]
    input_record_count: int
    output_record_count: int
    output_format: str
    target: str
    fasta_text: str
