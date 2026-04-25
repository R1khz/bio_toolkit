from __future__ import annotations

from typing import Any

from bio_toolkit.contracts.common.models import ContractModel


class AnalyzedRecord(ContractModel):
    sequence_id: str
    description: str
    molecule_type: str
    analysis: dict[str, Any]
