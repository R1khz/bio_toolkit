from typing import Any

from bio_toolkit.contracts.common.models import ContractModel
from bio_toolkit.contracts.search.models import SearchHit


class FetchPreview(ContractModel):
    accession: str
    database: str
    rettype: str
    preview: str


class AlphaFoldPayload(ContractModel):
    prediction: dict[str, Any] | None = None


class ProviderSearchPayload(ContractModel):
    results: list[SearchHit]
    database: str | None = None
    organism: str | None = None
    fetch_preview: FetchPreview | None = None
    top_hit_entry: dict[str, Any] | None = None
    sequence_preview: dict[str, Any] | None = None
    entry: dict[str, Any] | None = None
    alphafold: dict[str, Any] | None = None
