from pydantic import Field

from bio_toolkit.contracts.common.models import ContractModel


class AnnotateRequest(ContractModel):
    target: str
    source: str = "auto"
    input_format: str = "auto"
    database: str = ""
    rettype: str = ""
    feature_limit: int = Field(default=10, ge=1)
