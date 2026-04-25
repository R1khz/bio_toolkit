from bio_toolkit.contracts.common.models import ContractModel
from bio_toolkit.contracts.search.models import SearchHit


class SearchResponse(ContractModel):
    provider: str
    database_label: str
    result_count: int
    results: list[SearchHit]
