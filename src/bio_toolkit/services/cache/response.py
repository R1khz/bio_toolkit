from bio_toolkit.contracts.cache.models import CachedRecordSummary
from bio_toolkit.contracts.common.models import ContractModel


class CacheResponse(ContractModel):
    records: list[CachedRecordSummary] = []
    record: CachedRecordSummary | None = None
    preview: str | None = None
