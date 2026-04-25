from unittest.mock import patch

from bio_toolkit.services.search.request import SearchRequest
from bio_toolkit.services.search.service import run_search


def test_search_service_uses_provider_inference_for_auto() -> None:
    request = SearchRequest(
        query="P69905",
        provider="auto",
        database="protein",
        organism="",
        limit=5,
    )

    with patch("bio_toolkit.services.search.service.infer_search_provider", return_value="uniprot"):
        with patch("bio_toolkit.services.search.service.search_uniprot", return_value=[]):
            response = run_search(request, settings=None)

    assert response.provider == "uniprot"
    assert response.result_count == 0


def test_search_service_falls_back_to_genes_for_invalid_kegg_database() -> None:
    request = SearchRequest(
        query="hsa:10458",
        provider="kegg",
        database="protein",
        organism="",
        limit=5,
    )

    with patch("bio_toolkit.services.search.service.search_kegg", return_value=[]):
        response = run_search(request, settings=None)

    assert response.provider == "kegg"
    assert response.database_label == "KEGG:genes"
