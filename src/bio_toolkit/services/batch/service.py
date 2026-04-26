from __future__ import annotations

from pathlib import Path

from bio_toolkit.providers.ncbi.client import default_fetch_path
from bio_toolkit.services.analyze import AnalyzeRequest, run_analysis
from bio_toolkit.services.fetch import FetchRequest, run_fetch

from .request import BatchRequest
from .response import BatchResponse


def run_batch(request: BatchRequest, *, settings, status=None) -> BatchResponse:
    items = _read_batch_targets(Path(request.targets_file))
    normalized_mode = request.mode.strip().lower()
    if normalized_mode not in {"analyze", "fetch"}:
        raise ValueError("Unsupported batch mode. Use one of: analyze, fetch.")

    normalized_input_kind = request.input_kind.strip().lower()
    if normalized_input_kind not in {"auto", "accessions", "files"}:
        raise ValueError("Unsupported input kind. Use one of: auto, accessions, files.")
    if normalized_mode == "fetch" and normalized_input_kind == "files":
        raise ValueError("Fetch mode does not support --input-kind files.")

    status = status or _NullStatus()
    results = []
    status.update(f"Running batch {normalized_mode} on {len(items)} item(s)...")
    for raw_item in items:
        try:
            results.append(
                _run_batch_item(
                    raw_item=raw_item,
                    base_dir=Path(request.targets_file).resolve().parent,
                    mode=normalized_mode,
                    input_kind=normalized_input_kind,
                    settings=settings,
                    database=request.database,
                    rettype=request.rettype,
                    input_format=request.input_format,
                    min_orf_aa=request.min_orf_aa,
                    use_cache=request.use_cache,
                    refresh=request.refresh,
                )
            )
        except Exception as exc:
            results.append(
                {
                    "item": raw_item,
                    "status": "error",
                    "operation": normalized_mode,
                    "error": str(exc),
                }
            )
            if request.fail_fast:
                raise ValueError(f"Batch stopped at '{raw_item}': {exc}") from exc

    succeeded = sum(1 for item in results if item["status"] == "ok")
    failed = len(results) - succeeded
    return BatchResponse(
        mode=normalized_mode,
        input_kind=normalized_input_kind,
        targets_file=str(Path(request.targets_file).resolve()),
        database=request.database,
        rettype=request.rettype,
        total_items=len(results),
        succeeded=succeeded,
        failed=failed,
        results=results,
    )


def _read_batch_targets(targets_file: Path) -> list[str]:
    if not targets_file.exists():
        raise ValueError(f"Batch input file was not found: {targets_file}")
    items = []
    for line in targets_file.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        items.append(stripped)
    if not items:
        raise ValueError("Batch input file did not contain any usable items.")
    return items


def _run_batch_item(
    *,
    raw_item: str,
    base_dir: Path,
    mode: str,
    input_kind: str,
    settings,
    database: str,
    rettype: str,
    input_format: str,
    min_orf_aa: int,
    use_cache: bool,
    refresh: bool,
) -> dict:
    item_type, resolved_path = _resolve_batch_item_kind(
        raw_item=raw_item,
        base_dir=base_dir,
        input_kind=input_kind,
    )

    if item_type == "file":
        if mode == "fetch":
            raise ValueError("Fetch mode only accepts accession items.")
        analysis = run_analysis(
            AnalyzeRequest(
                target=str(resolved_path),
                source="file",
                input_format=input_format,
                min_orf_aa=min_orf_aa,
            ),
            settings=settings,
        )
        report = analysis.model_dump()
        return {
            "item": raw_item,
            "status": "ok",
            "operation": mode,
            "source_kind": "file",
            "label": str(resolved_path.resolve()),
            "input_format": report["input_format"],
            "record_count": report["record_count"],
            "molecule_types": sorted({record["molecule_type"] for record in report["records"]}),
            "analysis": report,
        }

    fetch_response = run_fetch(
        FetchRequest(
            accession=raw_item,
            database=database,
            rettype=rettype,
            use_cache=use_cache,
            refresh=refresh,
            save_cache=True,
        ),
        settings=settings,
    )

    if mode == "fetch":
        destination = _write_fetched_output(
            settings=settings,
            accession=raw_item,
            rettype=rettype,
            content=fetch_response.record.content,
        )
        return {
            "item": raw_item,
            "status": "ok",
            "operation": mode,
            "source_kind": "accession",
            "accession": fetch_response.record.accession,
            "database": fetch_response.record.database,
            "rettype": fetch_response.record.rettype,
            "retrieved_from": fetch_response.record.source,
            "saved_to": str(destination),
            "cache_path": fetch_response.cache_path,
        }

    analysis = run_analysis(
        AnalyzeRequest(
            target=raw_item,
            source="cache",
            database=database,
            rettype=rettype,
            min_orf_aa=min_orf_aa,
        ),
        settings=settings,
    )
    report = analysis.model_dump()
    return {
        "item": raw_item,
        "status": "ok",
        "operation": mode,
        "source_kind": "accession",
        "accession": fetch_response.record.accession,
        "database": fetch_response.record.database,
        "rettype": fetch_response.record.rettype,
        "retrieved_from": fetch_response.record.source,
        "record_count": report["record_count"],
        "molecule_types": sorted({record["molecule_type"] for record in report["records"]}),
        "analysis": report,
    }


def _resolve_batch_item_kind(
    *,
    raw_item: str,
    base_dir: Path,
    input_kind: str,
) -> tuple[str, Path | None]:
    if input_kind == "accessions":
        return "accession", None

    candidate = Path(raw_item)
    if not candidate.is_absolute():
        candidate = (base_dir / candidate).resolve()

    if input_kind == "files":
        if not candidate.exists():
            raise ValueError(f"Listed file was not found: {candidate}")
        return "file", candidate
    if candidate.exists():
        return "file", candidate
    return "accession", None


def _write_fetched_output(*, settings, accession: str, rettype: str, content: str) -> Path:
    destination = default_fetch_path(settings.output_dir, accession, rettype)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


class _NullStatus:
    def update(self, *_args, **_kwargs) -> None:
        return
