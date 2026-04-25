from pathlib import Path

from bio_toolkit.services.analyze.request import AnalyzeRequest
from bio_toolkit.services.analyze.service import run_analysis


def test_analyze_service_reads_local_file_and_returns_record_count(tmp_path: Path) -> None:
    fasta = tmp_path / "seq.fasta"
    fasta.write_text(">seq1\nATGGCCAAATGA\n", encoding="utf-8")

    request = AnalyzeRequest(
        target=str(fasta),
        source="file",
        input_format="auto",
        min_orf_aa=2,
    )
    response = run_analysis(request, settings=None)

    assert response.record_count == 1
    assert response.source.kind == "file"
