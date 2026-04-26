from bio_toolkit.contracts.common.models import ContractModel


class CacheRequest(ContractModel):
    accession: str | None = None
    database: str = ""
    rettype: str = ""
    preview_lines: int = 8
