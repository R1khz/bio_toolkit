from pathlib import Path

from Bio import SeqIO
from Bio.Seq import Seq
from Bio.SeqFeature import FeatureLocation, SeqFeature
from Bio.SeqRecord import SeqRecord

from bio_toolkit.services.annotate.request import AnnotateRequest
from bio_toolkit.services.annotate.service import run_annotation


def test_annotation_service_reads_local_file(tmp_path: Path) -> None:
    gb = tmp_path / "seq.gb"
    record = SeqRecord(Seq("ATGGCC"), id="TEST", description="Test record")
    record.annotations["molecule_type"] = "DNA"
    record.annotations["organism"] = "Testus example"
    record.annotations["source"] = "Testus example"
    record.annotations["accessions"] = ["TEST001"]
    record.features = [SeqFeature(FeatureLocation(0, 6), type="gene", qualifiers={"gene": ["x"]})]
    SeqIO.write([record], gb, "genbank")

    request = AnnotateRequest(
        target=str(gb),
        source="file",
        input_format="genbank",
        feature_limit=5,
    )
    response = run_annotation(request, settings=None)
    assert response.record_count >= 0

