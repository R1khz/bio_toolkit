import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from bio_toolkit.cache_store import CacheStore  # noqa: E402
from bio_toolkit.ncbi import FetchResult  # noqa: E402


class CacheStoreTests(unittest.TestCase):
    def test_save_and_reload_cached_record(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CacheStore(Path(tmpdir))
            fetched = FetchResult(
                accession="NM_000001.1",
                database="nucleotide",
                rettype="fasta",
                content=">NM_000001.1\nATGC\n",
                file_suffix=".fasta",
            )

            saved_record = store.save_fetch_result(fetched)
            loaded = store.load_fetch_result(
                accession="NM_000001.1",
                database="nucleotide",
                rettype="fasta",
            )

            self.assertIsNotNone(loaded)
            cache_record, cached_result = loaded
            self.assertEqual(saved_record.accession, cache_record.accession)
            self.assertEqual(cached_result.source, "cache")
            self.assertEqual(cached_result.content, fetched.content)
            self.assertTrue(store.resolve_content_path(cache_record).exists())

    def test_list_records_respects_filters(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = CacheStore(Path(tmpdir))
            store.save_fetch_result(
                FetchResult(
                    accession="NM_000001.1",
                    database="nucleotide",
                    rettype="fasta",
                    content=">NM_000001.1\nATGC\n",
                    file_suffix=".fasta",
                )
            )
            store.save_fetch_result(
                FetchResult(
                    accession="NP_000001.1",
                    database="protein",
                    rettype="fasta",
                    content=">NP_000001.1\nMSTN\n",
                    file_suffix=".fasta",
                )
            )

            nucleotide_only = store.list_records(database="nucleotide")
            protein_only = store.list_records(database="protein")

            self.assertEqual(len(nucleotide_only), 1)
            self.assertEqual(len(protein_only), 1)
            self.assertEqual(nucleotide_only[0].database, "nucleotide")
            self.assertEqual(protein_only[0].database, "protein")


if __name__ == "__main__":
    unittest.main()
