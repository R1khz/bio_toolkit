from __future__ import annotations

from typing import Any

from bio_toolkit.contracts.analyze.models import AnalyzedRecord
from bio_toolkit.contracts.common.models import SourceRef
from bio_toolkit.domain.analysis.sequence_analyzer import SequenceAnalyzer
from bio_toolkit.providers.alphafold.client import AlphaFoldError, fetch_alphafold_prediction
from bio_toolkit.providers.uniprot.client import (
    UniProtError,
    extract_uniprot_protein_context,
    fetch_uniprot_entry,
    is_uniprot_accession,
)

from .helpers import load_analysis_input
from .request import AnalyzeRequest
from .response import AnalyzeResponse


def run_analysis(request: AnalyzeRequest, *, settings: Any) -> AnalyzeResponse:
    records, resolved_format, source_info = load_analysis_input(request, settings=settings)
    analyzed_records = SequenceAnalyzer(
        min_orf_aa=request.min_orf_aa,
        custom_motifs=request.motifs or None,
    ).analyze_records(records)
    _enrich_protein_analysis_records(analyzed_records, source_info)
    return AnalyzeResponse(
        source=SourceRef(**source_info),
        input_format=resolved_format,
        record_count=len(analyzed_records),
        records=[AnalyzedRecord.model_validate(record) for record in analyzed_records],
    )


def _enrich_protein_analysis_records(
    records: list[dict[str, Any]], source_info: dict[str, Any]
) -> None:
    enrichment_cache: dict[str, tuple[dict[str, Any], dict[str, Any] | None]] = {}
    for record in records:
        if record.get("molecule_type") != "PROTEIN":
            continue

        accession = _protein_enrichment_accession(record, source_info)
        if not accession:
            continue

        if accession not in enrichment_cache:
            try:
                entry = fetch_uniprot_entry(accession)
                protein_context = extract_uniprot_protein_context(entry)
            except UniProtError:
                protein_context = {}

            try:
                alphafold_context = fetch_alphafold_prediction(accession)
            except AlphaFoldError:
                alphafold_context = None

            enrichment_cache[accession] = (protein_context, alphafold_context)

        protein_context, alphafold_context = enrichment_cache[accession]
        analysis = record.setdefault("analysis", {})
        domains = analysis.get("domains")
        if isinstance(domains, dict) and not domains.get("skipped"):
            external_domains = protein_context.get("domains", [])
            merged_domains = _merge_domain_lists(domains.get("all_domains", []), external_domains)
            domains["all_domains"] = merged_domains[:10]
            domains["domains_found"] = len(merged_domains)
            domains["uniprot_domains"] = len(external_domains)

        analysis["external"] = {
            "uniprot": protein_context or None,
            "alphafold": alphafold_context,
        }


def _protein_enrichment_accession(
    record: dict[str, Any], source_info: dict[str, Any]
) -> str | None:
    candidates = [
        source_info.get("accession"),
        record.get("sequence_id"),
        str(record.get("description", "")).split()[0] if record.get("description") else "",
    ]
    provider = str(source_info.get("provider", "")).strip().lower()

    for candidate in candidates:
        normalized = _normalize_uniprot_candidate(candidate)
        if normalized is not None:
            return normalized

    if provider == "uniprot":
        fallback = str(source_info.get("label") or "").strip()
        if fallback:
            return fallback

    return None


def _normalize_uniprot_candidate(value: object) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None

    token = text.split()[0]
    parts = [token]
    if "|" in token:
        parts.extend(part for part in token.split("|") if part)

    for part in parts:
        candidate = part.strip()
        if is_uniprot_accession(candidate):
            return candidate.upper()

    return None


def _merge_domain_lists(
    local_domains: list[dict[str, Any]],
    external_domains: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged = []
    seen = set()

    for item in local_domains + external_domains:
        key = (
            str(item.get("name")),
            item.get("start_aa"),
            item.get("end_aa"),
            str(item.get("source")),
        )
        if key in seen:
            continue
        seen.add(key)
        merged.append(item)

    return merged
