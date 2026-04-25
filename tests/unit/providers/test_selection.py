from bio_toolkit.providers.selection import (
    infer_query_provider,
    infer_search_provider,
    normalize_query_provider,
)


def test_selection_module_keeps_current_provider_rules() -> None:
    assert infer_query_provider("P69905") == "uniprot"
    assert infer_search_provider("BRCA1") == "ncbi"
    assert normalize_query_provider("alphafold") == "alphafold"
