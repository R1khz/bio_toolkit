from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from bio_toolkit.ncbi import FetchResult, normalize_rettype, validate_database


class CacheError(RuntimeError):
    """Raised when cache state cannot be read or written."""


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
        return build_cache_key(self.accession, self.database, self.rettype)


class CacheStore:
    def __init__(self, cache_dir: Path) -> None:
        self.cache_dir = cache_dir
        self.index_path = self.cache_dir / "index.json"

    def save_fetch_result(self, result: FetchResult, *, source: str = "ncbi") -> CacheRecord:
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        relative_path = self._relative_path(
            accession=result.accession,
            database=result.database,
            rettype=result.rettype,
            file_suffix=result.file_suffix,
        )
        absolute_path = self.cache_dir / relative_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_text(result.content, encoding="utf-8")

        record = CacheRecord(
            accession=result.accession,
            database=validate_database(result.database),
            rettype=normalize_rettype(result.rettype),
            source=source,
            fetched_at=_utc_now_iso(),
            content_path=str(relative_path),
            file_size=absolute_path.stat().st_size,
        )

        index = self._load_index()
        index["records"][record.cache_key] = asdict(record)
        self._save_index(index)
        return record

    def list_records(self, *, database: str = "", rettype: str = "") -> list[CacheRecord]:
        index = self._load_index()
        records = [self._record_from_dict(item) for item in index["records"].values()]

        if database:
            validated_db = validate_database(database)
            records = [record for record in records if record.database == validated_db]

        if rettype:
            validated_rettype = normalize_rettype(rettype)
            records = [record for record in records if record.rettype == validated_rettype]

        return sorted(records, key=lambda item: item.fetched_at, reverse=True)

    def get_record(self, *, accession: str, database: str, rettype: str) -> CacheRecord | None:
        index = self._load_index()
        cache_key = build_cache_key(accession, database, rettype)
        raw_record = index["records"].get(cache_key)
        if raw_record is None:
            return None
        return self._record_from_dict(raw_record)

    def find_records_by_accession(self, accession: str) -> list[CacheRecord]:
        index = self._load_index()
        matches = []
        for raw_record in index["records"].values():
            if str(raw_record.get("accession", "")).strip() == accession.strip():
                matches.append(self._record_from_dict(raw_record))
        return sorted(matches, key=lambda item: item.fetched_at, reverse=True)

    def load_fetch_result(
        self,
        *,
        accession: str,
        database: str,
        rettype: str,
    ) -> tuple[CacheRecord, FetchResult] | None:
        record = self.get_record(accession=accession, database=database, rettype=rettype)
        if record is None:
            return None

        absolute_path = self.resolve_content_path(record)
        if not absolute_path.exists():
            raise CacheError(f"Cached file is missing: {absolute_path}")

        result = FetchResult(
            accession=record.accession,
            database=record.database,
            rettype=record.rettype,
            content=absolute_path.read_text(encoding="utf-8"),
            file_suffix=absolute_path.suffix,
            source="cache",
        )
        return record, result

    def resolve_content_path(self, record: CacheRecord) -> Path:
        return self.cache_dir / record.content_path

    def _load_index(self) -> dict[str, Any]:
        if not self.index_path.exists():
            return {"version": 1, "records": {}}

        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CacheError(f"Cache index is not valid JSON: {self.index_path}") from exc

        data.setdefault("version", 1)
        data.setdefault("records", {})
        return data

    def _save_index(self, data: dict[str, Any]) -> None:
        self.index_path.write_text(json.dumps(data, indent=2, sort_keys=True), encoding="utf-8")

    def _record_from_dict(self, raw: dict[str, Any]) -> CacheRecord:
        return CacheRecord(
            accession=str(raw["accession"]),
            database=validate_database(str(raw["database"])),
            rettype=normalize_rettype(str(raw["rettype"])),
            source=str(raw.get("source", "ncbi")),
            fetched_at=str(raw["fetched_at"]),
            content_path=str(raw["content_path"]),
            file_size=int(raw["file_size"]),
        )

    def _relative_path(
        self,
        *,
        accession: str,
        database: str,
        rettype: str,
        file_suffix: str,
    ) -> Path:
        safe_accession = _safe_filename(accession)
        return (
            Path(validate_database(database))
            / normalize_rettype(rettype)
            / f"{safe_accession}{file_suffix}"
        )


def build_cache_key(accession: str, database: str, rettype: str) -> str:
    return f"{validate_database(database)}::{normalize_rettype(rettype)}::{accession.strip()}"


def _safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())


def _utc_now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()
