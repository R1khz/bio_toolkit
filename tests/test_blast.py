import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cli import app  # noqa: E402
from bio_toolkit.ncbi import BlastHit, BlastSearchInfo, BlastSubmission  # noqa: E402


class FakeBlastClient:
    def blast_submit(
        self,
        *,
        program: str,
        database: str,
        query: str,
        hitlist_size: int = 10,
        expect: float = 10.0,
    ) -> BlastSubmission:
        self.last_query = query
        return BlastSubmission(
            rid="TEST-RID-001",
            rtoe_seconds=24,
            program=program,
            database=database,
            hitlist_size=hitlist_size,
            expect=expect,
        )

    def blast_fetch_results(self, *, rid: str):
        return [
            BlastHit(
                query_id="queryA",
                subject_id="P68871.2",
                percent_identity=100.0,
                alignment_length=147,
                mismatches=0,
                gap_opens=0,
                query_start=1,
                query_end=147,
                subject_start=1,
                subject_end=147,
                e_value="5.82e-106",
                bit_score=301.0,
                query_coverage=100.0,
            )
        ]


class BlastCommandTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_blast_local_file_and_export_csv(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            fasta = tmp_path / "query.fasta"
            export_path = tmp_path / "blast.csv"
            fasta.write_text(
                (">queryA\nMVHLTPEEKSAVTALWGKVNVDEVGGEALGRLLVVYPWTQRFFESFGDLSTPDAVMGNPKV\n"),
                encoding="utf-8",
            )

            with patch("bio_toolkit.cli._build_ncbi_client", return_value=FakeBlastClient()):
                with patch(
                    "bio_toolkit.cli._wait_for_remote_blast",
                    return_value=(
                        BlastSearchInfo(rid="TEST-RID-001", status="READY", there_are_hits=True),
                        60,
                        1,
                    ),
                ):
                    result = self.runner.invoke(
                        app,
                        [
                            "blast",
                            str(fasta),
                            "--poll-interval",
                            "60",
                            "--timeout-seconds",
                            "120",
                            "--output",
                            str(export_path),
                            "--export-format",
                            "csv",
                        ],
                    )

            self.assertEqual(result.exit_code, 0, msg=result.stdout)
            self.assertIn("Remote BLAST", result.stdout)
            self.assertIn("BLAST Hits", result.stdout)
            self.assertTrue(export_path.exists())
            exported = export_path.read_text(encoding="utf-8")
            self.assertIn("TEST-RID-001", exported)
            self.assertIn("P68871.2", exported)


if __name__ == "__main__":
    unittest.main()
