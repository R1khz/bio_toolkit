from bio_toolkit.contracts.common.models import ContractModel


class FetchRequest(ContractModel):
    accession: str
    database: str = "nucleotide"
    rettype: str = "fasta"
    use_cache: bool = True
    refresh: bool = False
    save_cache: bool = True
