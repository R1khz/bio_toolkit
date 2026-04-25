from __future__ import annotations

from typing import Any

from bio_toolkit.contracts.common.models import ContractModel


class TransformMetadata(ContractModel):
    operation: str
    frame: int | None = None
    to_stop: bool | None = None
    start: int | None = None
    end: int | None = None


class TransformPreviewRecord(ContractModel):
    sequence_id: str
    description: str
    length: int
    molecule_type: str
    analysis: dict[str, Any] | None = None
