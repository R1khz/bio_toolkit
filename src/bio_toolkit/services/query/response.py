from typing import Any

from pydantic import model_serializer

from bio_toolkit.contracts.common.models import ContractModel
from bio_toolkit.contracts.query.models import AlphaFoldPayload, ProviderSearchPayload


class QueryResponse(ContractModel):
    provider: str
    kind: str
    query: str
    result_count: int
    payload: ProviderSearchPayload | AlphaFoldPayload

    @model_serializer(mode="plain")
    def serialize(self) -> dict[str, Any]:
        data = {
            "provider": self.provider,
            "kind": self.kind,
            "query": self.query,
            "result_count": self.result_count,
        }
        data.update(self.payload.model_dump(include=self.payload.model_fields_set))
        return data
