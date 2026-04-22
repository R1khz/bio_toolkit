import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.kegg import search_kegg  # noqa: E402


class KeggTests(unittest.TestCase):
    def test_search_kegg_handles_direct_identifiers(self) -> None:
        payload = (
            "ENTRY       hsa:10458\n"
            "NAME        BAIAP2L1\n"
            "DEFINITION  BAI1-associated protein 2-like 1\n"
            "ORGANISM    hsa  Homo sapiens (human)\n"
        )

        with patch("bio_toolkit.kegg._request_text", return_value=payload) as request_text:
            results = search_kegg(query="hsa:10458", database="genes", limit=5)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].accession, "hsa:10458")
        self.assertEqual(results[0].database, "genes")
        self.assertEqual(results[0].organism, "Homo sapiens (human)")
        self.assertIn("BAI1-associated protein", results[0].title)
        request_text.assert_called_once()


if __name__ == "__main__":
    unittest.main()
