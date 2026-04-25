from bio_toolkit.contracts.common.models import ContractModel


class TransformRequest(ContractModel):
    target: str
    operation: str = "reverse-complement"
    source: str = "auto"
    input_format: str = "auto"
    database: str = ""
    rettype: str = ""
    frame: int = 1
    to_stop: bool = False
    start: int = 1
    end: int = 0
