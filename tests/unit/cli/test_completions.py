import json
from pathlib import Path

from bio_toolkit.cli.completions import complete_cached_accession


def _write_index(tmp_path: Path, accessions: list[str]) -> Path:
    records = {
        f"nucleotide::fasta::{acc}": {
            "accession": acc,
            "database": "nucleotide",
            "rettype": "fasta",
            "source": "ncbi",
            "fetched_at": "2026-01-01T00:00:00+00:00",
            "file_size": 100,
            "content_path": f"nucleotide/fasta/{acc}.fasta",
        }
        for acc in accessions
    }
    index = tmp_path / "index.json"
    index.write_text(json.dumps({"records": records, "version": 1}), encoding="utf-8")
    return tmp_path


def test_returns_all_accessions_when_incomplete_is_empty(tmp_path, monkeypatch):
    cache_dir = _write_index(tmp_path, ["NG_005905", "NM_001346216", "YDX66035"])
    monkeypatch.setenv("BIO_TOOLKIT_CACHE_DIR", str(cache_dir))
    result = complete_cached_accession("")
    assert sorted(result) == ["NG_005905", "NM_001346216", "YDX66035"]


def test_filters_by_prefix(tmp_path, monkeypatch):
    cache_dir = _write_index(tmp_path, ["NG_005905", "NM_001346216", "YDX66035"])
    monkeypatch.setenv("BIO_TOOLKIT_CACHE_DIR", str(cache_dir))
    result = complete_cached_accession("NM_")
    assert result == ["NM_001346216"]


def test_returns_empty_list_when_no_match(tmp_path, monkeypatch):
    cache_dir = _write_index(tmp_path, ["NG_005905", "NM_001346216"])
    monkeypatch.setenv("BIO_TOOLKIT_CACHE_DIR", str(cache_dir))
    result = complete_cached_accession("XYZ")
    assert result == []


def test_returns_empty_list_when_cache_missing(tmp_path, monkeypatch):
    monkeypatch.setenv("BIO_TOOLKIT_CACHE_DIR", str(tmp_path / "nonexistent"))
    monkeypatch.chdir(tmp_path)
    result = complete_cached_accession("NM_")
    assert result == []


def test_returns_empty_list_when_index_is_invalid_json(tmp_path, monkeypatch):
    cache_dir = tmp_path
    (cache_dir / "index.json").write_text("not json", encoding="utf-8")
    monkeypatch.setenv("BIO_TOOLKIT_CACHE_DIR", str(cache_dir))
    result = complete_cached_accession("")
    assert result == []
