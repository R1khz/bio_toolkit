from __future__ import annotations

import time
from typing import Any

from bio_toolkit.contracts.blast.models import BlastHitRecord
from bio_toolkit.contracts.common.models import SourceRef
from bio_toolkit.domain.analysis import detect_molecule_type
from bio_toolkit.ncbi import BlastSearchInfo, NcbiClient, NcbiError, blast_hits_to_dict
from bio_toolkit.services.analyze.helpers import load_analysis_input
from bio_toolkit.services.analyze.request import AnalyzeRequest
from bio_toolkit.storage.files import dump_records_to_text

from .request import BlastRequest
from .response import BlastResponse


def run_blast(
    request: BlastRequest,
    *,
    settings: Any,
    status=None,
    ncbi_client: NcbiClient | None = None,
    waiter=None,
) -> BlastResponse:
    records, resolved_format, source_info = load_analysis_input(
        AnalyzeRequest(
            target=request.target,
            source=request.source,
            input_format=request.input_format,
            database=request.cache_database,
            rettype=request.cache_rettype,
        ),
        settings=settings,
    )

    return run_blast_records(
        records=records,
        resolved_format=resolved_format,
        source_info=source_info,
        program=request.program,
        blast_database=request.blast_database,
        hitlist_size=request.hitlist_size,
        expect=request.expect,
        poll_interval=request.poll_interval,
        timeout_seconds=request.timeout_seconds,
        settings=settings,
        status=status,
        ncbi_client=ncbi_client,
        waiter=waiter,
    )


def run_blast_records(
    *,
    records,
    resolved_format: str,
    source_info: dict[str, Any],
    program: str,
    blast_database: str,
    hitlist_size: int,
    expect: float,
    poll_interval: int,
    timeout_seconds: int,
    settings: Any,
    status=None,
    ncbi_client: NcbiClient | None = None,
    waiter=None,
) -> BlastResponse:
    if poll_interval < 60:
        raise ValueError("poll_interval must be at least 60 seconds to respect NCBI guidance.")
    if timeout_seconds < 1:
        raise ValueError("timeout_seconds must be at least 1.")

    query_kind, molecule_types = _resolve_blast_query_kind(records)
    resolved_program = _resolve_blast_program(program, query_kind=query_kind)
    resolved_blast_database = _resolve_blast_database(blast_database, program=resolved_program)

    client = ncbi_client or _build_ncbi_client(settings)
    wait = waiter or _wait_for_remote_blast
    query_text = dump_records_to_text(records, output_format="fasta")
    status = status or _NullStatus()
    status.update("Submitting remote BLAST to NCBI...")

    submission = client.blast_submit(
        program=resolved_program,
        database=resolved_blast_database,
        query=query_text,
        hitlist_size=hitlist_size,
        expect=expect,
    )
    search_info, elapsed_seconds, poll_count = wait(
        client=client,
        status=status,
        submission=submission,
        poll_interval=poll_interval,
        timeout_seconds=timeout_seconds,
    )
    hits = []
    if search_info.status == "READY" and search_info.there_are_hits is not False:
        status.update(f"RID {submission.rid} is ready. Downloading BLAST results...")
        hits = client.blast_fetch_results(rid=submission.rid)

    query_records = [
        {
            "sequence_id": record.id,
            "description": record.description,
            "molecule_type": _detect_molecule_type(record),
            "length": len(record.seq),
        }
        for record in records
    ]
    hit_payload = blast_hits_to_dict(hits)
    return BlastResponse(
        source=SourceRef(**source_info),
        input_format=resolved_format,
        query={
            "record_count": len(records),
            "query_kind": query_kind,
            "molecule_types": molecule_types,
            "records": query_records,
        },
        blast={
            "rid": submission.rid,
            "program": submission.program,
            "database": submission.database,
            "status": search_info.status,
            "there_are_hits": search_info.there_are_hits,
            "estimated_time_seconds": submission.rtoe_seconds,
            "poll_interval_seconds": poll_interval,
            "timeout_seconds": timeout_seconds,
            "elapsed_seconds": elapsed_seconds,
            "poll_count": poll_count,
        },
        hit_count=len(hit_payload),
        hits=[BlastHitRecord.model_validate(item) for item in hit_payload],
    )


def _build_ncbi_client(settings: Any) -> NcbiClient:
    return NcbiClient.from_settings(settings)


def _wait_for_remote_blast(
    *,
    client: NcbiClient,
    status,
    submission,
    poll_interval: int,
    timeout_seconds: int,
) -> tuple[BlastSearchInfo, int, int]:
    start_time = time.monotonic()
    poll_count = 0
    next_poll_at = start_time + max(poll_interval, submission.rtoe_seconds)

    while True:
        now = time.monotonic()
        elapsed_seconds = int(now - start_time)
        if elapsed_seconds >= timeout_seconds:
            raise NcbiError(
                f"Remote BLAST job {submission.rid} did not finish within "
                f"{timeout_seconds} seconds."
            )

        remaining_seconds = max(0, int(next_poll_at - now))
        status.update(
            " | ".join(
                [
                    f"RID {submission.rid}",
                    f"estimated {submission.rtoe_seconds}s",
                    f"next check in {remaining_seconds}s",
                    f"elapsed {elapsed_seconds}s",
                ]
            )
        )
        if remaining_seconds > 0:
            time.sleep(min(1.0, float(remaining_seconds)))
            continue

        poll_count += 1
        search_info = client.blast_check_status(rid=submission.rid)
        if search_info.status == "READY":
            return search_info, elapsed_seconds, poll_count
        if search_info.status == "FAILED":
            raise NcbiError(f"Remote BLAST job {submission.rid} failed on NCBI.")
        if search_info.status == "UNKNOWN":
            raise NcbiError(f"Remote BLAST job {submission.rid} returned UNKNOWN status.")

        next_poll_at = time.monotonic() + poll_interval


def _resolve_blast_query_kind(records) -> tuple[str, list[str]]:
    molecule_types = sorted({_detect_molecule_type(record) for record in records})
    if not molecule_types or "UNKNOWN" in molecule_types:
        raise ValueError("BLAST query type could not be determined from the input records.")
    if set(molecule_types) <= {"DNA", "RNA"}:
        return "nucleotide", molecule_types
    if molecule_types == ["PROTEIN"]:
        return "protein", molecule_types
    raise ValueError("BLAST input cannot mix nucleotide and protein query records.")


def _resolve_blast_program(program: str, *, query_kind: str) -> str:
    normalized = program.strip().lower()
    if normalized in {"", "auto"}:
        return "blastp" if query_kind == "protein" else "blastn"

    allowed_for_query = {
        "protein": {"blastp", "tblastn"},
        "nucleotide": {"blastn", "blastx", "tblastx"},
    }
    if normalized not in allowed_for_query[query_kind]:
        allowed = ", ".join(sorted(allowed_for_query[query_kind]))
        raise ValueError(
            f"Program '{program}' is incompatible with a {query_kind} query. Use one of: {allowed}."
        )
    return normalized


def _resolve_blast_database(blast_database: str, *, program: str) -> str:
    normalized = blast_database.strip()
    if normalized and normalized.lower() != "auto":
        return normalized
    if program in {"blastp", "blastx"}:
        return "swissprot"
    return "core_nt"


def _detect_molecule_type(record) -> str:
    return detect_molecule_type(record)


class _NullStatus:
    def update(self, *_args, **_kwargs) -> None:
        return
