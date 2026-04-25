from bio_toolkit.cli import app
from bio_toolkit.config import get_settings
from bio_toolkit.providers import infer_query_provider, normalize_search_provider


def test_new_package_names_exist() -> None:
    assert hasattr(app, "command")
    assert callable(get_settings)
    assert infer_query_provider("P69905") == "uniprot"
    assert normalize_search_provider("ncbi") == "ncbi"
