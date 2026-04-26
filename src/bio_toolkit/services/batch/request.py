from bio_toolkit.contracts.common.models import ContractModel


class BatchRequest(ContractModel):
    targets_file: str
    mode: str = "analyze"
    input_kind: str = "auto"
    database: str = "nucleotide"
    rettype: str = "fasta"
    input_format: str = "auto"
    min_orf_aa: int = 30
    use_cache: bool = True
    refresh: bool = False
    fail_fast: bool = False
