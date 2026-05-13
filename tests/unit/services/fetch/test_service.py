from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import Mock

from bio_toolkit.ncbi import FetchResult
from bio_toolkit.services.fetch.request import FetchRequest
from bio_toolkit.services.fetch.service import run_fetch
from bio_toolkit.storage.cache import CacheStore


def test_fetch_service_prefers_cache_before_remote_fetch() -> None:
    request = FetchRequest(
        accession="NM_000546",
        database="nucleotide",
        rettype="fasta",
        use_cache=True,
        refresh=False,
        save_cache=True,
    )
    cached_fetch = FetchResult(
        accession="NM_000546",
        database="nucleotide",
        rettype="fasta",
        content=">NM_000546\nATGC\n",
        file_suffix=".fasta",
        source="ncbi",
    )
    cache_store = Mock()
    cache_record = SimpleNamespace(content_path="nucleotide/fasta/NM_000546.fasta")
    cache_store.load_fetch_result.return_value = (cache_record, cached_fetch)
    cache_store.resolve_content_path.return_value = Path("/tmp/cache/NM_000546.fasta")

    response = run_fetch(
        request,
        settings=None,
        cache_store=cache_store,
        ncbi_client=Mock(),
    )

    assert response.accession == "NM_000546"
    assert response.cache_hit is True
    assert response.record.content == ">NM_000546\nATGC\n"
    assert response.record.provider == "ncbi"


def test_fetch_service_saves_remote_result_when_cache_misses() -> None:
    request = FetchRequest(
        accession="NM_000546",
        database="nucleotide",
        rettype="fasta",
        use_cache=True,
        refresh=False,
        save_cache=True,
    )
    fetched = FetchResult(
        accession="NM_000546",
        database="nucleotide",
        rettype="fasta",
        content=">NM_000546\nATGC\n",
        file_suffix=".fasta",
        source="ncbi",
    )
    ncbi_client = Mock()
    ncbi_client.fetch.return_value = fetched

    with TemporaryDirectory() as tmp_dir:
        settings = SimpleNamespace(cache_dir=Path(tmp_dir))
        response = run_fetch(request, settings=settings, ncbi_client=ncbi_client)

        assert response.cache_hit is False
        assert response.cache_path is not None
        assert response.record.source == "ncbi"
        assert response.record.provider == "ncbi"
        assert CacheStore(Path(tmp_dir)).get_record(
            accession="NM_000546",
            database="nucleotide",
            rettype="fasta",
        ) is not None
