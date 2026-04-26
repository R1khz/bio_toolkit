from bio_toolkit.contracts.batch.models import BatchResultRecord
from bio_toolkit.contracts.common.models import ContractModel


class BatchResponse(ContractModel):
    mode: str
    input_kind: str
    targets_file: str
    database: str
    rettype: str
    total_items: int
    succeeded: int
    failed: int
    results: list[BatchResultRecord]
