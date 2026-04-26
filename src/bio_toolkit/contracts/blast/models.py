from bio_toolkit.contracts.common.models import ContractModel


class BlastHitRecord(ContractModel):
    query_id: str
    subject_id: str
    percent_identity: float
    alignment_length: int
    mismatches: int
    gap_opens: int
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    e_value: str
    bit_score: float
    query_coverage: float | None = None
