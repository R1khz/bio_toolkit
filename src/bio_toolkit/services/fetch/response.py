from bio_toolkit.contracts.common.models import ContractModel
from bio_toolkit.contracts.fetch.models import FetchedRecord


class FetchResponse(ContractModel):
    accession: str
    cache_hit: bool
    record: FetchedRecord
    cache_path: str | None = None
