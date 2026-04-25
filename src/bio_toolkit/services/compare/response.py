from typing import Any

from bio_toolkit.contracts.common.models import ContractModel
from bio_toolkit.contracts.compare.models import ComparedRecord


class CompareResponse(ContractModel):
    target_count: int
    record_count: int
    targets: list[dict[str, Any]]
    records: list[ComparedRecord]
    comparison: dict[str, Any]
