import os
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.ncbi import (  # noqa: E402
    BlastHit,
    BlastSearchInfo,
    BlastSubmission,
    NcbiClient,
    SearchResult,
    build_search_term,
    default_fetch_path,
    parse_blast_tabular_csv,
)


class FakeNcbiClient(NcbiClient):
    def __init__(self) -> None:
        super().__init__(email="tester@example.com")
        self.json_calls: list[tuple[str, dict[str, str]]] = []
        self.text_calls: list[tuple[str, dict[str, str]]] = []

    def _request_json(self, endpoint: str, params: dict[str, str]):
        self.json_calls.append((endpoint, params))
        if endpoint == "esearch.fcgi":
            return {"esearchresult": {"idlist": ["NM_000001.1", "NM_000002.1"]}}

        return {
            "result": {
                "uids": ["1", "2"],
                "1": {
                    "uid": "1",
                    "caption": "NM_000001.1",
                    "title": "example transcript [Homo sapiens]",
                    "sourcedb": "refseq",
                    "slen": "1863",
                },
                "2": {
                    "uid": "2",
                    "extra": "gi|2|ref|NM_000002.1|",
                    "title": "example transcript 2 [Mus musculus]",
                },
            }
        }

    def _request_text(self, endpoint: str, params: dict[str, str]) -> str:
        self.text_calls.append((endpoint, params))
        return ">NM_000001.1\nATGC\n"


class FakeBlastNcbiClient(NcbiClient):
    def __init__(self) -> None:
        super().__init__(email="tester@example.com")
        self.absolute_calls: list[tuple[str, dict[str, str], str]] = []

    def _request_text_absolute(
        self,
        url: str,
        params: dict[str, str],
        *,
        method: str = "GET",
        already_encoded: bool = False,
    ) -> str:
        self.absolute_calls.append((url, params, method))
        if params.get("CMD") == "Put":
            return """
            <!--QBlastInfoBegin
            RID = TEST-RID-001
            RTOE = 24
            QBlastInfoEnd-->
            """
        if params.get("FORMAT_OBJECT") == "SearchInfo":
            return """
            <!--QBlastInfoBegin
            Status=READY
            QBlastInfoEnd-->
            <!--QBlastInfoBegin
            ThereAreHits=yes
            QBlastInfoEnd-->
            """
        return "queryA,P68871.2,100.000,147,0,0,1,147,1,147,5.82e-106,301,100.00\n"


class NcbiTests(unittest.TestCase):
    def test_build_search_term_adds_organism_filter(self) -> None:
        self.assertEqual(
            build_search_term("BRCA1", "Homo sapiens"),
            "(BRCA1) AND (Homo sapiens[Organism])",
        )

    def test_search_normalizes_summary_payload(self) -> None:
        client = FakeNcbiClient()

        results = client.search(
            database="nucleotide",
            query="BRCA1",
            organism="Homo sapiens",
            limit=5,
        )

        self.assertEqual(len(results), 2)
        self.assertIsInstance(results[0], SearchResult)
        self.assertEqual(results[0].accession, "NM_000001.1")
        self.assertEqual(results[0].organism, "Homo sapiens")
        self.assertEqual(results[0].source_db, "refseq")
        self.assertEqual(results[0].length, 1863)
        self.assertEqual(results[1].accession, "NM_000002.1")
        self.assertEqual(results[1].organism, "Mus musculus")
        self.assertEqual(client.json_calls[0][0], "esearch.fcgi")
        self.assertEqual(client.json_calls[1][0], "esummary.fcgi")
        self.assertEqual(client.json_calls[0][1]["db"], "nucleotide")
        self.assertEqual(client.json_calls[0][1]["retmax"], "5")

    def test_fetch_builds_default_output_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            self.assertEqual(
                default_fetch_path(output_dir, "NM_000001.1", "fasta"),
                output_dir / "NM_000001.1.fasta",
            )
            self.assertEqual(
                default_fetch_path(output_dir, "NM_000001.1", "gb"),
                output_dir / "NM_000001.1.gb",
            )

    def test_blast_submit_parses_rid_and_rtoe(self) -> None:
        client = FakeBlastNcbiClient()

        submission = client.blast_submit(
            program="blastp",
            database="swissprot",
            query=">queryA\nMKWVTFISLL\n",
            hitlist_size=5,
            expect=1e-5,
        )

        self.assertIsInstance(submission, BlastSubmission)
        self.assertEqual(submission.rid, "TEST-RID-001")
        self.assertEqual(submission.rtoe_seconds, 24)
        self.assertEqual(submission.program, "blastp")
        self.assertEqual(submission.database, "swissprot")
        self.assertEqual(client.absolute_calls[0][2], "POST")

    def test_blast_status_parses_ready_and_hits(self) -> None:
        client = FakeBlastNcbiClient()

        search_info = client.blast_check_status(rid="TEST-RID-001")

        self.assertIsInstance(search_info, BlastSearchInfo)
        self.assertEqual(search_info.status, "READY")
        self.assertTrue(search_info.there_are_hits)

    def test_parse_blast_csv_rows(self) -> None:
        hits = parse_blast_tabular_csv(
            (
                "queryA,P68871.2,100.000,147,0,0,1,147,1,147,5.82e-106,301,100.00\n"
                "queryA,P02024.2,99.320,147,1,0,1,147,1,147,2.03e-105,300,100.00\n"
            )
        )

        self.assertEqual(len(hits), 2)
        self.assertIsInstance(hits[0], BlastHit)
        self.assertEqual(hits[0].query_id, "queryA")
        self.assertEqual(hits[0].subject_id, "P68871.2")
        self.assertEqual(hits[0].alignment_length, 147)
        self.assertEqual(hits[0].e_value, "5.82e-106")
        self.assertEqual(hits[0].query_coverage, 100.0)


if __name__ == "__main__":
    unittest.main()
