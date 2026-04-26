from bio_toolkit.contracts.common.models import ContractModel


class BlastRequest(ContractModel):
    target: str
    source: str = "auto"
    input_format: str = "auto"
    cache_database: str = ""
    cache_rettype: str = ""
    program: str = "auto"
    blast_database: str = "auto"
    hitlist_size: int = 10
    expect: float = 10.0
    poll_interval: int = 60
    timeout_seconds: int = 1800
