from .client import (
    UniProtError,
    extract_uniprot_protein_context,
    fetch_uniprot_entry,
    fetch_uniprot_fasta,
    is_uniprot_accession,
    search_uniprot,
    summarize_uniprot_entry,
)

__all__ = [
    "UniProtError",
    "extract_uniprot_protein_context",
    "fetch_uniprot_entry",
    "fetch_uniprot_fasta",
    "is_uniprot_accession",
    "search_uniprot",
    "summarize_uniprot_entry",
]
