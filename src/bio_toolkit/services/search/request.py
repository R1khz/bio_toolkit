from pydantic import Field

from bio_toolkit.contracts.common.models import ContractModel


class SearchRequest(ContractModel):
    query: str
    provider: str = "ncbi"
    database: str = "nucleotide"
    organism: str = ""
    limit: int = Field(default=10, ge=1, le=100)
