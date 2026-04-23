import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.kegg import KeggError  # noqa: E402
from bio_toolkit.ncbi import SearchResult  # noqa: E402
from bio_toolkit.provider_queries import build_provider_query_report  # noqa: E402

SETTINGS = SimpleNamespace(
    ncbi_email="tester@example.com",
    ncbi_tool_name="bio-toolkit",
    ncbi_api_key="",
)


class ProviderQueryTests(unittest.TestCase):
    def test_build_uniprot_report_for_accession_enriches_alphafold(self) -> None:
        entry = {
            "primaryAccession": "P69905",
            "uniProtkbId": "HBA_HUMAN",
            "entryType": "UniProtKB reviewed (Swiss-Prot)",
            "proteinDescription": {
                "recommendedName": {"fullName": {"value": "Hemoglobin subunit alpha"}}
            },
            "organism": {"scientificName": "Homo sapiens"},
            "sequence": {"length": 142, "value": "M" * 142},
            "features": [],
            "comments": [],
            "genes": [{"geneName": {"value": "HBA1"}}],
            "keywords": [{"name": "Oxygen transport"}],
        }

        with patch("bio_toolkit.provider_queries.fetch_uniprot_entry", return_value=entry):
            with patch(
                "bio_toolkit.provider_queries.fetch_alphafold_prediction",
                return_value={"model_id": "AF-P69905-F1"},
            ):
                report = build_provider_query_report(
                    settings=SETTINGS,
                    provider="uniprot",
                    query="P69905",
                )

        self.assertEqual(report["provider"], "uniprot")
        self.assertEqual(report["kind"], "entry")
        self.assertEqual(report["entry"]["accession"], "P69905")
        self.assertTrue(report["entry"]["reviewed"])
        self.assertEqual(report["alphafold"]["model_id"], "AF-P69905-F1")

    def test_build_kegg_report_for_identifier_returns_entry(self) -> None:
        payload = (
            "ENTRY       hsa:10458\n"
            "NAME        BAIAP2L1\n"
            "DEFINITION  BAI1-associated protein 2-like 1\n"
            "ORGANISM    hsa Homo sapiens (human)\n"
            "PATHWAY     hsa04520 Adherens junction\n"
            "DBLINKS     UniProt: Q9UQB8\n"
        )

        with patch("bio_toolkit.provider_queries.fetch_kegg_entry", return_value=payload):
            with patch(
                "bio_toolkit.provider_queries.fetch_kegg_sequence",
                side_effect=KeggError("no sequence"),
            ):
                report = build_provider_query_report(
                    settings=SETTINGS,
                    provider="kegg",
                    query="hsa:10458",
                    database="genes",
                )

        self.assertEqual(report["provider"], "kegg")
        self.assertEqual(report["kind"], "entry")
        self.assertEqual(report["entry"]["accession"], "hsa:10458")
        self.assertEqual(report["entry"]["organism"], "Homo sapiens (human)")

    def test_build_ncbi_report_uses_exact_accession_preview(self) -> None:
        results = [
            SearchResult(
                accession="NM_000001.1",
                title="example transcript",
                organism="Homo sapiens",
                source_db="refseq",
                uid="1",
                length=100,
                provider="ncbi",
                database="nucleotide",
            )
        ]
        fetched = SimpleNamespace(
            accession="NM_000001.1",
            database="nucleotide",
            rettype="fasta",
            content=">NM_000001.1\nATGC\n",
        )
        fake_client = SimpleNamespace(
            search=lambda **_: results,
            fetch=lambda **_: fetched,
        )

        with patch(
            "bio_toolkit.provider_queries.NcbiClient.from_settings",
            return_value=fake_client,
        ):
            report = build_provider_query_report(
                settings=SETTINGS,
                provider="ncbi",
                query="NM_000001.1",
                database="nucleotide",
            )

        self.assertEqual(report["provider"], "ncbi")
        self.assertEqual(report["result_count"], 1)
        self.assertEqual(report["fetch_preview"]["accession"], "NM_000001.1")

    def test_build_alphafold_report(self) -> None:
        with patch(
            "bio_toolkit.provider_queries.fetch_alphafold_prediction",
            return_value={"model_id": "AF-P69905-F1", "accession": "P69905"},
        ):
            report = build_provider_query_report(
                settings=SETTINGS,
                provider="alphafold",
                query="P69905",
            )

        self.assertEqual(report["provider"], "alphafold")
        self.assertEqual(report["prediction"]["model_id"], "AF-P69905-F1")


if __name__ == "__main__":
    unittest.main()
