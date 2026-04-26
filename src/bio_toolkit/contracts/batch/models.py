from typing import Any

from bio_toolkit.contracts.common.models import ContractModel


class BatchResultRecord(ContractModel):
    item: str
    status: str
    operation: str
    source_kind: str | None = None
    label: str | None = None
    accession: str | None = None
    database: str | None = None
    rettype: str | None = None
    retrieved_from: str | None = None
    saved_to: str | None = None
    cache_path: str | None = None
    input_format: str | None = None
    record_count: int | None = None
    molecule_types: list[str] | None = None
    analysis: dict[str, Any] | None = None
    error: str | None = None
