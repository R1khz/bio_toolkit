from typing import Any

from bio_toolkit.contracts.common.models import ContractModel


class StartResponse(ContractModel):
    kind: str
    payload: dict[str, Any]
