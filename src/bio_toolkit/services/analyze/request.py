from pydantic import Field

from bio_toolkit.contracts.common.models import ContractModel


class AnalyzeRequest(ContractModel):
    target: str
    source: str = "auto"
    input_format: str = "auto"
    database: str = ""
    rettype: str = ""
    min_orf_aa: int = Field(default=30, ge=1)
    motifs: list[str] = Field(default_factory=list)
