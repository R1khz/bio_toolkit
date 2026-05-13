from __future__ import annotations

import json
import os
from pathlib import Path


def complete_cached_accession(incomplete: str) -> list[str]:
    index = _find_index()
    if index is None:
        return []
    try:
        data = json.loads(index.read_text(encoding="utf-8"))
        records = data["records"]
        return [
            meta["accession"]
            for meta in records.values()
            if meta["accession"].startswith(incomplete)
        ]
    except Exception:
        return []


def _find_index() -> Path | None:
    candidates = [
        _from_env(),
        Path(".cache") / "bio-toolkit" / "index.json",
        Path.home() / ".cache" / "bio-toolkit" / "index.json",
    ]
    for path in candidates:
        if path is not None and path.exists():
            return path
    return None


def _from_env() -> Path | None:
    value = os.environ.get("BIO_TOOLKIT_CACHE_DIR", "").strip()
    if not value:
        return None
    return Path(value) / "index.json"
