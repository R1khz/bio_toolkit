import pytest
from pydantic import ValidationError

from bio_toolkit.contracts.common.models import (
    ExportArtifact,
    ProviderRef,
    SourceRef,
    WarningItem,
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
