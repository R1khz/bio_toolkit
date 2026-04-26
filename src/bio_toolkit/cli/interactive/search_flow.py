from __future__ import annotations

from types import SimpleNamespace

from rich.console import Console
from rich.panel import Panel

from bio_toolkit.config import ensure_runtime_dirs
from bio_toolkit.contracts.analyze.models import AnalyzedRecord
from bio_toolkit.contracts.annotate.models import AnnotatedRecord
from bio_toolkit.contracts.common.models import SourceRef
from bio_toolkit.domain.analysis.sequence_analyzer import SequenceAnalyzer
from bio_toolkit.domain.annotations import build_annotation_report
from bio_toolkit.providers.alphafold.client import fetch_alphafold_prediction
from bio_toolkit.providers.kegg.client import fetch_kegg_sequence
from bio_toolkit.providers.uniprot.client import fetch_uniprot_fasta
from bio_toolkit.services.analyze import AnalyzeResponse
from bio_toolkit.services.annotate import AnnotateResponse
from bio_toolkit.services.blast.service import run_blast_records
from bio_toolkit.services.fetch import FetchRequest, run_fetch
from bio_toolkit.services.query import QueryRequest, run_query
from bio_toolkit.storage.files import format_from_rettype, load_records_from_text

from ...services.analyze.service import _enrich_protein_analysis_records
from ..presenters.analysis_presenter import render_analysis_response
from ..presenters.annotation_presenter import render_annotation_response
from ..presenters.blast_presenter import render_blast_response
from ..presenters.fetch_presenter import render_fetch_response
from ..presenters.query_presenter import render_query_response
from .picker import (
    InteractivePickerCancelled,
    InteractivePickerError,
    pick_post_search_action,
    pick_search_result,
)


def run_interactive_search_flow(
    *,
    console: Console,
    settings,
    database: str,
    results,
) -> None:
    try:
        selected_result = pick_search_result(results)
        action = pick_post_search_action(selected_result)
    except InteractivePickerCancelled:
        console.print("[yellow]Interactive selection cancelled.[/yellow]")
        return
    except InteractivePickerError as exc:
        console.print(f"[red]{exc}[/red]")
        return

    if action == "print_accession":
        console.print(selected_result.accession)
        return

    if action == "query_details":
        response = run_query(
            QueryRequest(
                query=selected_result.accession,
                provider=str(getattr(selected_result, "provider", "auto")),
                database=str(getattr(selected_result, "database", "") or database or "auto"),
                organism=str(getattr(selected_result, "organism", "") or ""),
                limit=1,
                rettype="fasta",
            ),
            settings=settings,
        )
        render_query_response(console=console, response=response, as_json=False)
        return

    ensure_runtime_dirs(settings)
    fetch_response, record = _fetch_interactive_result(
        settings=settings,
        result=selected_result,
        database=database,
        action=action,
    )

    if action in {"fetch", "fetch_analyze"}:
        render_fetch_response(
            console=console,
            settings=settings,
            response=fetch_response,
            output=None,
            stdout=False,
            preview_lines=6,
        )

    if action in {"analyze", "fetch_analyze"}:
        render_analysis_response(
            console=console,
            response=_analyze_fetched_record(record),
            as_json=False,
            exported_path=None,
            export_format=None,
        )
        return

    if action == "annotate":
        render_annotation_response(
            console=console,
            response=_annotate_fetched_record(record),
            as_json=False,
            exported_path=None,
            export_format=None,
        )
        return

    if action == "blast":
        with console.status("Submitting remote BLAST to NCBI...") as status:
            blast_response = _blast_fetched_record(record, settings=settings, status=status)
        render_blast_response(
            console=console,
            response=blast_response,
            as_json=False,
            exported_path=None,
            export_format=None,
        )
        return

    if action == "alphafold":
        _render_alphafold_lookup(console, selected_result.accession)


def _interactive_fetch_rettype(action: str, result) -> str:
    provider = str(getattr(result, "provider", "ncbi")).strip().lower()
    if provider == "ncbi" and action == "annotate":
        return "gb"
    return "fasta"


def _fetch_interactive_result(*, settings, result, database: str, action: str):
    provider = str(getattr(result, "provider", "ncbi")).strip().lower()
    rettype = _interactive_fetch_rettype(action, result)

    if provider == "ncbi":
        response = run_fetch(
            FetchRequest(
                accession=result.accession,
                database=database,
                rettype=rettype,
                use_cache=True,
                refresh=False,
                save_cache=True,
            ),
            settings=settings,
        )
        return response, response.record

    record = (
        fetch_uniprot_fasta(result.accession)
        if provider == "uniprot"
        else fetch_kegg_sequence(result.accession)
    )
    response = SimpleNamespace(
        accession=record.accession,
        record=SimpleNamespace(
            accession=record.accession,
            database=record.database,
            rettype=record.rettype,
            source=record.source,
            content=record.content,
        ),
        cache_path=None,
    )
    return response, record


def _analyze_fetched_record(record) -> AnalyzeResponse:
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=format_from_rettype(record.rettype),
    )
    analyzed_records = SequenceAnalyzer(min_orf_aa=30).analyze_records(records)
    source_info = {
        "kind": record.source,
        "label": record.accession,
        "accession": record.accession,
        "database": record.database,
        "provider": record.provider,
        "rettype": record.rettype,
    }
    _enrich_protein_analysis_records(analyzed_records, source_info)
    return AnalyzeResponse(
        source=SourceRef(**source_info),
        input_format=resolved_format,
        record_count=len(analyzed_records),
        records=[AnalyzedRecord.model_validate(item) for item in analyzed_records],
    )


def _annotate_fetched_record(record) -> AnnotateResponse:
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=format_from_rettype(record.rettype),
    )
    report = build_annotation_report(
        records=records,
        input_format=resolved_format,
        source_info={
            "kind": record.source,
            "label": record.accession,
            "accession": record.accession,
            "database": record.database,
            "provider": record.provider,
            "rettype": record.rettype,
        },
        feature_limit=10,
    )
    return AnnotateResponse(
        source=SourceRef(**report["source"]),
        input_format=report["input_format"],
        record_count=report["record_count"],
        feature_limit=report["feature_limit"],
        records=[AnnotatedRecord.model_validate(item) for item in report["records"]],
    )


def _blast_fetched_record(record, *, settings, status):
    records, resolved_format = load_records_from_text(
        record.content,
        input_format=format_from_rettype(record.rettype),
    )
    return run_blast_records(
        records=records,
        resolved_format=resolved_format,
        source_info={
            "kind": record.source,
            "label": record.accession,
            "accession": record.accession,
            "database": record.database,
            "provider": record.provider,
            "rettype": record.rettype,
        },
        program="auto",
        blast_database="auto",
        hitlist_size=10,
        expect=10.0,
        poll_interval=60,
        timeout_seconds=1800,
        settings=settings,
        status=status,
    )


def _render_alphafold_lookup(console: Console, accession: str) -> None:
    prediction = fetch_alphafold_prediction(accession)
    if prediction is None:
        console.print(
            Panel.fit(
                f"No AlphaFold prediction was found for {accession}.",
                title="AlphaFold",
            )
        )
        return

    lines = [
        f"Accession: {prediction['accession']}",
        f"Model ID: {prediction['model_id']}",
        f"Entry: {prediction['entry_url']}",
    ]
    if prediction.get("avg_plddt") is not None:
        lines.append(f"Average pLDDT: {prediction['avg_plddt']}")
    if prediction.get("sequence_start") is not None and prediction.get("sequence_end") is not None:
        lines.append(
            f"Sequence range: {prediction['sequence_start']} - {prediction['sequence_end']}"
        )
    console.print(Panel.fit("\n".join(lines), title="AlphaFold"))
