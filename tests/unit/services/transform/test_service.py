from pathlib import Path

from bio_toolkit.services.transform.request import TransformRequest
from bio_toolkit.services.transform.service import run_transform


def test_transform_service_reverse_complements_local_file(tmp_path: Path) -> None:
    fasta = tmp_path / "seq.fasta"
    fasta.write_text(">seq1\nATGC\n", encoding="utf-8")

    response = run_transform(
        TransformRequest(
            target=str(fasta),
            operation="reverse-complement",
            source="file",
        ),
        settings=None,
    )

    assert response.output_record_count == 1
    assert response.parameters["operation"] == "reverse-complement"
    assert "GCAT" in response.fasta_text
