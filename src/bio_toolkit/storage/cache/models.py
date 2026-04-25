from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CacheRecord:
    accession: str
    database: str
    rettype: str
    source: str
    fetched_at: str
    content_path: str
    file_size: int

    @property
    def cache_key(self) -> str:
        from .store import build_cache_key

        return build_cache_key(self.accession, self.database, self.rettype)
