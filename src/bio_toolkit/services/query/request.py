from pydantic import Field

from bio_toolkit.contracts.common.models import ContractModel


class QueryRequest(ContractModel):
    query: str
    provider: str = "auto"
    database: str = "auto"
    organism: str = ""
    limit: int = Field(default=5, ge=1, le=100)
    rettype: str = "fasta"
