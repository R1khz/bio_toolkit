from typing import Any

from bio_toolkit.contracts.blast.models import BlastHitRecord
from bio_toolkit.contracts.common.models import ContractModel, SourceRef


class BlastResponse(ContractModel):
    source: SourceRef
    input_format: str
    query: dict[str, Any]
    blast: dict[str, Any]
    hit_count: int
    hits: list[BlastHitRecord]
