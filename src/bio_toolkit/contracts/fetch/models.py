from bio_toolkit.contracts.common.models import ContractModel


class FetchedRecord(ContractModel):
    accession: str
    database: str
    rettype: str
    source: str
    provider: str
    content: str
