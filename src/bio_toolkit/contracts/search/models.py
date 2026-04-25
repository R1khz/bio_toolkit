from bio_toolkit.contracts.common.models import ContractModel


class SearchHit(ContractModel):
    accession: str
    title: str
    organism: str | None = None
    length: int | None = None
