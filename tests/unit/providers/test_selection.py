import pytest

import bio_toolkit.legacy_providers as legacy_providers
import bio_toolkit.providers as providers
import bio_toolkit.providers.alphafold as alphafold_provider
import bio_toolkit.providers.kegg as kegg_provider
import bio_toolkit.providers.ncbi as ncbi_provider
import bio_toolkit.providers.uniprot as uniprot_provider
from bio_toolkit.providers.errors import ProviderSelectionError
from bio_toolkit.providers.selection import (
    infer_query_provider,
    infer_search_provider,
    normalize_search_provider,
    normalize_query_provider,
)


def test_selection_module_keeps_current_provider_rules() -> None:
    assert infer_query_provider("P69905") == "uniprot"
    assert infer_search_provider("BRCA1") == "ncbi"
    assert normalize_query_provider("alphafold") == "alphafold"


def test_selection_module_raises_provider_selection_error() -> None:
    with pytest.raises(ProviderSelectionError):
        normalize_search_provider("bad-provider")

    with pytest.raises(ProviderSelectionError):
        normalize_query_provider("bad-provider")


def test_root_provider_package_reexports_provider_selection_error() -> None:
    assert providers.ProviderSelectionError is ProviderSelectionError


def test_provider_adapter_packages_expose_expected_symbols() -> None:
    assert ncbi_provider.SearchResult is not None
    assert ncbi_provider.BlastSubmission is not None
    assert ncbi_provider.BlastSearchInfo is not None
    assert ncbi_provider.BlastHit is not None
    assert ncbi_provider.SUPPORTED_RETTYPES is not None
    assert ncbi_provider.SUPPORTED_BLAST_PROGRAMS is not None
    assert ncbi_provider.default_fetch_path is not None
    assert ncbi_provider.blast_hits_to_dict is not None
    assert ncbi_provider.parse_blast_tabular_csv is not None

    assert uniprot_provider.fetch_uniprot_fasta is not None
    assert uniprot_provider.extract_uniprot_protein_context is not None

    assert kegg_provider.KeggNotFoundError is not None
    assert kegg_provider.search_kegg is not None

    assert alphafold_provider.AlphaFoldError is not None
    assert alphafold_provider.fetch_alphafold_prediction is not None


def test_legacy_providers_selection_compatibility_still_works() -> None:
    assert legacy_providers.infer_query_provider("P69905") == "uniprot"
    assert legacy_providers.infer_search_provider("BRCA1") == "ncbi"
    assert legacy_providers.normalize_query_provider("alphafold") == "alphafold"
