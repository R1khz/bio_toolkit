from __future__ import annotations

import re

from bio_toolkit.kegg import SUPPORTED_KEGG_DATABASES, is_kegg_identifier, normalize_kegg_database
from bio_toolkit.uniprot import is_uniprot_accession

from .errors import ProviderSelectionError

SUPPORTED_SEARCH_PROVIDERS = {"auto", "ncbi", "uniprot", "kegg"}
SUPPORTED_QUERY_PROVIDERS = SUPPORTED_SEARCH_PROVIDERS | {"alphafold"}

DNA_QUERY_CHARS = set("ATCGNRYSWKMBDHV-")
RNA_QUERY_CHARS = set("AUCGNRYSWKMBDHV-")
PROTEIN_QUERY_CHARS = set("ACDEFGHIKLMNPQRSTVWYBZX*-")


def normalize_search_provider(provider: str) -> str:
    resolved = provider.strip().lower()
    if resolved not in SUPPORTED_SEARCH_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_SEARCH_PROVIDERS))
        raise ProviderSelectionError(
            f"Unsupported search provider '{provider}'. Use one of: {allowed}."
        )
    return resolved


def normalize_query_provider(provider: str) -> str:
    resolved = provider.strip().lower()
    if resolved not in SUPPORTED_QUERY_PROVIDERS:
        allowed = ", ".join(sorted(SUPPORTED_QUERY_PROVIDERS))
        raise ProviderSelectionError(
            f"Unsupported query provider '{provider}'. Use one of: {allowed}."
        )
    return resolved


def infer_query_input(query: str) -> dict[str, str]:
    clean_query = re.sub(r"\s+", "", query).upper()
    if len(clean_query) < 12:
        return {"kind": "text", "molecule_type": "UNKNOWN", "normalized": query.strip()}

    chars = set(clean_query)
    if chars and chars <= RNA_QUERY_CHARS and "U" in chars:
        return {"kind": "sequence", "molecule_type": "RNA", "normalized": clean_query}
    if chars and chars <= DNA_QUERY_CHARS:
        return {"kind": "sequence", "molecule_type": "DNA", "normalized": clean_query}
    if chars and chars <= PROTEIN_QUERY_CHARS:
        return {"kind": "sequence", "molecule_type": "PROTEIN", "normalized": clean_query}
    return {"kind": "text", "molecule_type": "UNKNOWN", "normalized": query.strip()}


def infer_search_provider(query: str) -> str:
    clean_query = query.strip()
    if is_uniprot_accession(clean_query):
        return "uniprot"
    if is_kegg_identifier(clean_query):
        return "kegg"

    query_info = infer_query_input(clean_query)
    if query_info["kind"] == "sequence" and query_info["molecule_type"] == "PROTEIN":
        return "uniprot"
    return "ncbi"


def infer_query_provider(query: str) -> str:
    return infer_search_provider(query)


def normalize_kegg_search_database(database: str) -> str:
    return normalize_kegg_database(database)


def supported_kegg_databases_text() -> str:
    return ", ".join(sorted(SUPPORTED_KEGG_DATABASES))


def supported_query_providers_text() -> str:
    ordered = ["auto", "ncbi", "uniprot", "kegg", "alphafold"]
    return ", ".join(item for item in ordered if item in SUPPORTED_QUERY_PROVIDERS)
