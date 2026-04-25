from __future__ import annotations

from typing import Any

from bio_toolkit.contracts.common.models import ContractModel


class AnnotatedRecord(ContractModel):
    sequence_id: str
    accession: str
    description: str
    input_format: str
    molecule_type: str
    sequence_length: int
    organism: str
    taxonomy: list[str]
    keywords: list[str]
    topology: str
    date: str
    source: str
    gene_names: list[str]
    product_names: list[str]
    feature_count: int
    feature_counts: dict[str, int]
    selected_features: list[dict[str, Any]]
