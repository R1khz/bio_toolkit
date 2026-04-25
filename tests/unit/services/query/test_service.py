from unittest.mock import patch

from bio_toolkit.services.query.request import QueryRequest
from bio_toolkit.services.query.service import run_query


def test_query_service_returns_typed_provider_response() -> None:
    request = QueryRequest(query="P69905", provider="alphafold")

    with patch(
        "bio_toolkit.services.query.service.fetch_alphafold_prediction",
        return_value={"model_id": "AF-P69905-F1"},
    ):
        response = run_query(request, settings=None)

    assert response.provider == "alphafold"
    assert response.result_count == 1
    assert response.payload.prediction["model_id"] == "AF-P69905-F1"
