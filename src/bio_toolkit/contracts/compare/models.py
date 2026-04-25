from __future__ import annotations

from typing import Any

from bio_toolkit.contracts.common.models import ContractModel


class ComparedRecord(ContractModel):
    source: dict[str, Any]
    sequence_id: str
    description: str
    molecule_type: str
    analysis: dict[str, Any]
