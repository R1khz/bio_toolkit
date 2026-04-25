from unittest.mock import patch

import bio_toolkit.cli as cli
import bio_toolkit.legacy_cli as legacy_cli
from bio_toolkit.cli import app
from bio_toolkit.config import get_settings
from bio_toolkit.providers import infer_query_provider, normalize_search_provider


def test_new_package_names_exist() -> None:
    assert hasattr(app, "command")
    assert callable(get_settings)
    assert infer_query_provider("P69905") == "uniprot"
    assert normalize_search_provider("ncbi") == "ncbi"


def test_cli_package_prepopulates_forwarded_symbols() -> None:
    assert "search_kegg" in cli.__dict__
    assert cli.search_kegg is legacy_cli.search_kegg


def test_cli_patch_target_restores_legacy_symbol_after_patch() -> None:
    original = legacy_cli.search_kegg

    with patch("bio_toolkit.cli.search_kegg", autospec=True) as mocked:
        assert cli.search_kegg is mocked
        assert legacy_cli.search_kegg is mocked

    assert cli.search_kegg is original
    assert legacy_cli.search_kegg is original


def test_cli_star_import_preserves_legacy_exports() -> None:
    namespace: dict[str, object] = {}

    exec("from bio_toolkit.cli import *", {}, namespace)

    assert namespace["app"] is app
    assert namespace["search_kegg"] is legacy_cli.search_kegg
