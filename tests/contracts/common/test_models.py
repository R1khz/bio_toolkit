import pytest
from pydantic import ValidationError

from bio_toolkit.contracts.common import (
    ExportArtifact,
    ProviderRef,
    SourceRef,
    WarningItem,
)
from bio_toolkit.shared.errors import (
    BioToolkitError,
    ProviderAdapterError,
    ServiceError,
    StorageAdapterError,
)


def test_common_contracts_are_strict_and_frozen() -> None:
    provider = ProviderRef(name="ncbi")
    source = SourceRef(kind="file", label="/tmp/input.fasta")
    artifact = ExportArtifact(format="json", path="outputs/report.json")
    warning = WarningItem(
        code="tm-unavailable",
        message="Melting temperature unavailable",
    )

    assert provider.name == "ncbi"
    assert source.kind == "file"
    assert artifact.format == "json"
    assert warning.code == "tm-unavailable"

    with pytest.raises(ValidationError):
        SourceRef(kind="file", label="/tmp/input.fasta", extra_field="boom")

    with pytest.raises(ValidationError, match="Instance is frozen"):
        provider.name = "uniprot"


def test_shared_error_exports_expose_expected_taxonomy() -> None:
    assert issubclass(ProviderAdapterError, BioToolkitError)
    assert issubclass(StorageAdapterError, BioToolkitError)
    assert issubclass(ServiceError, BioToolkitError)
