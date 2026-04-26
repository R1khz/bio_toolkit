from bio_toolkit.contracts.common.models import ContractModel


class CachedRecordSummary(ContractModel):
    accession: str
    database: str
    rettype: str
    source: str
    fetched_at: str
    content_path: str
    file_size: int
