import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.ncbi import SearchResult  # noqa: E402
from bio_toolkit.providers import infer_query_input, infer_search_provider  # noqa: E402
from bio_toolkit.services.search.request import SearchRequest  # noqa: E402
from bio_toolkit.services.search.service import run_search  # noqa: E402


class ProviderInferenceTests(unittest.TestCase):
    def test_infers_sequence_literals(self) -> None:
        self.assertEqual(infer_query_input("ATGCGTATGCGT")["molecule_type"], "DNA")
        self.assertEqual(infer_query_input("AUGCGUAUGCGU")["molecule_type"], "RNA")
        self.assertEqual(infer_query_input("MKWVTFISLLLL")["molecule_type"], "PROTEIN")

    def test_infers_provider_from_accessions(self) -> None:
        self.assertEqual(infer_search_provider("P69905"), "uniprot")
        self.assertEqual(infer_search_provider("hsa:10458"), "kegg")
        self.assertEqual(infer_search_provider("BRCA1"), "ncbi")

    def test_auto_provider_falls_back_to_genes_for_kegg_queries(self) -> None:
        fake_results = [
            SearchResult(
                accession="hsa:10458",
                title="example",
                organism="hsa",
                source_db="kegg:genes",
                uid="hsa:10458",
                provider="kegg",
                database="genes",
            )
        ]

        request = SearchRequest(
            provider="auto",
            query="hsa:10458",
            database="nucleotide",
            organism="",
            limit=5,
        )

        kegg_path = "bio_toolkit.services.search.service.search_kegg"
        with patch(kegg_path, return_value=fake_results) as search_kegg:
            response = run_search(request, settings=object())

        self.assertEqual(response.database_label, "KEGG:genes")
        search_kegg.assert_called_once_with(query="hsa:10458", database="genes", limit=5)


if __name__ == "__main__":
    unittest.main()
