from pydantic import Field

from bio_toolkit.contracts.common.models import ContractModel


class CompareRequest(ContractModel):
    targets: list[str] = Field(min_length=2)
    source: str = "auto"
    input_format: str = "auto"
    database: str = ""
    rettype: str = ""
    min_orf_aa: int = Field(default=30, ge=1)
