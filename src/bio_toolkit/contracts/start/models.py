from bio_toolkit.contracts.common.models import ContractModel


class GuidedStartInput(ContractModel):
    mode: str
    query: str
    provider: str
    database: str
    organism: str
    limit: int
