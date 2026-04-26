from bio_toolkit.contracts.common.models import ContractModel


class StartRequest(ContractModel):
    mode: str
    query: str
    provider: str
    database: str
    organism: str = ""
    limit: int = 10
