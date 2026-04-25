from pathlib import Path

from bio_toolkit.services.compare.request import CompareRequest
from bio_toolkit.services.compare.service import run_compare


def test_compare_service_reads_two_local_files(tmp_path: Path) -> None:
    fasta_a = tmp_path / "a.fasta"
    fasta_b = tmp_path / "b.fasta"
    fasta_a.write_text(">a\nATGCGTATGCGT\n", encoding="utf-8")
    fasta_b.write_text(">b\nATGGCCATTGTA\n", encoding="utf-8")

    response = run_compare(
        CompareRequest(targets=[str(fasta_a), str(fasta_b)], source="file", min_orf_aa=2),
        settings=None,
    )

    assert response.record_count == 2
    assert response.comparison["length"] is not None

