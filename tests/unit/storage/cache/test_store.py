from pathlib import Path
from tempfile import TemporaryDirectory

from bio_toolkit.ncbi import FetchResult
from bio_toolkit.storage.cache.store import CacheStore


def test_cache_store_save_and_load_round_trip() -> None:
    with TemporaryDirectory() as tmpdir:
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

        assert loaded is not None
        record, cached_result = loaded
        assert record == saved_record
        assert cached_result.content == fetched.content
        assert cached_result.source == "cache"
        assert store.resolve_content_path(record).exists()


def test_cache_store_list_records_respects_filters() -> None:
    with TemporaryDirectory() as tmpdir:
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

        assert len(nucleotide_only) == 1
        assert len(protein_only) == 1
        assert nucleotide_only[0].database == "nucleotide"
        assert protein_only[0].database == "protein"
