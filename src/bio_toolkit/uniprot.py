from __future__ import annotations

import json
import re
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bio_toolkit.ncbi import FetchResult, SearchResult, validate_limit

UNIPROT_API_BASE_URL = "https://rest.uniprot.org/uniprotkb"
UNIPROT_SEARCH_FIELDS = "accession,id,protein_name,organism_name,length"


class UniProtError(RuntimeError):
    """Raised when a UniProt request or response fails."""


def search_uniprot(
    *,
    query: str,
    organism: str = "",
    limit: int = 10,
    timeout_seconds: float = 20.0,
) -> list[SearchResult]:
    resolved_limit = validate_limit(limit)
    params = {
        "query": _build_uniprot_query(query, organism),
        "format": "json",
        "size": str(resolved_limit),
        "fields": UNIPROT_SEARCH_FIELDS,
    }
    payload = _request_json(f"{UNIPROT_API_BASE_URL}/search", params, timeout_seconds)

    results = []
    for item in payload.get("results", []):
        accession = str(item.get("primaryAccession") or item.get("uniProtkbId") or "-")
        results.append(
            SearchResult(
                accession=accession,
                title=_protein_name(item),
                organism=_organism_name(item),
                source_db="uniprotkb",
                uid=accession,
                length=_safe_int(item.get("sequence", {}).get("length")),
                provider="uniprot",
                database="protein",
            )
        )

    return results


def fetch_uniprot_fasta(
    accession: str,
    *,
    timeout_seconds: float = 20.0,
) -> FetchResult:
    clean_accession = accession.strip()
    if not clean_accession:
        raise ValueError("UniProt accession cannot be empty.")

    content = _request_text(
        f"{UNIPROT_API_BASE_URL}/{clean_accession}.fasta",
        timeout_seconds=timeout_seconds,
    )
    if not content.strip():
        raise UniProtError("UniProt returned an empty FASTA record.")

    return FetchResult(
        accession=clean_accession,
        database="protein",
        rettype="fasta",
        content=content,
        file_suffix=".fasta",
        source="uniprot",
        provider="uniprot",
    )


def fetch_uniprot_entry(
    accession: str,
    *,
    timeout_seconds: float = 20.0,
) -> dict[str, Any]:
    clean_accession = accession.strip()
    if not clean_accession:
        raise ValueError("UniProt accession cannot be empty.")

    return _request_json(
        f"{UNIPROT_API_BASE_URL}/{clean_accession}.json",
        {},
        timeout_seconds,
    )


def extract_uniprot_protein_context(entry: dict[str, Any]) -> dict[str, Any]:
    genes = []
    for gene in entry.get("genes", []):
        gene_name = gene.get("geneName", {}).get("value")
        if gene_name:
            genes.append(str(gene_name))

    keywords = [str(item.get("name")) for item in entry.get("keywords", []) if item.get("name")]

    return {
        "accession": str(entry.get("primaryAccession") or "-"),
        "protein_name": _protein_name(entry),
        "organism": _organism_name(entry),
        "genes": genes,
        "keywords": keywords,
        "domains": _extract_domain_features(entry.get("features", [])),
    }


def summarize_uniprot_entry(entry: dict[str, Any]) -> dict[str, Any]:
    context = extract_uniprot_protein_context(entry)
    sequence = entry.get("sequence", {})
    return {
        "accession": context["accession"],
        "entry_id": str(entry.get("uniProtkbId") or "-"),
        "protein_name": context["protein_name"],
        "organism": context["organism"],
        "genes": context["genes"],
        "keywords": context["keywords"],
        "domains": context["domains"],
        "functions": _extract_comment_text(
            entry,
            {"FUNCTION", "CATALYTIC ACTIVITY", "PATHWAY"},
        ),
        "subcellular_locations": _extract_comment_text(entry, {"SUBCELLULAR LOCATION"}),
        "cross_references": _extract_cross_references(entry),
        "sequence_length": _safe_int(sequence.get("length")),
        "sequence_preview": _sequence_preview(sequence.get("value")),
        "reviewed": _is_reviewed_entry(entry),
        "protein_existence": _protein_existence(entry),
    }


def is_uniprot_accession(value: str) -> bool:
    clean_value = value.strip().upper()
    if not clean_value:
        return False

    patterns = [
        r"^[OPQ][0-9][A-Z0-9]{3}[0-9]$",
        r"^[A-NR-Z][0-9][A-Z][A-Z0-9]{2}[0-9]$",
        r"^[A-NR-Z][0-9](?:[A-Z0-9]{3}[0-9]){2}$",
    ]
    return any(re.fullmatch(pattern, clean_value) for pattern in patterns)


def _build_uniprot_query(query: str, organism: str = "") -> str:
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty.")

    if not organism.strip():
        return clean_query

    return f"({clean_query}) AND (organism_name:{organism.strip()})"


def _protein_name(entry: dict[str, Any]) -> str:
    description = entry.get("proteinDescription", {})
    recommended = description.get("recommendedName", {})
    submitted_names = description.get("submissionNames", [])

    full_name = recommended.get("fullName", {}).get("value")
    if full_name:
        return str(full_name)

    for submitted in submitted_names:
        candidate = submitted.get("fullName", {}).get("value")
        if candidate:
            return str(candidate)

    return str(entry.get("uniProtkbId") or entry.get("primaryAccession") or "-")


def _organism_name(entry: dict[str, Any]) -> str:
    organism = entry.get("organism", {})
    return str(organism.get("scientificName") or "-")


def _extract_domain_features(features: list[dict[str, Any]]) -> list[dict[str, Any]]:
    domains = []
    for feature in features:
        category = str(feature.get("category") or "").upper()
        feature_type = str(feature.get("type") or "")
        if category != "DOMAINS_AND_SITES" and feature_type.lower() not in {
            "domain",
            "region",
            "repeat",
            "zinc finger",
            "motif",
        }:
            continue

        location = feature.get("location", {})
        start_aa = _location_value(location.get("start"))
        end_aa = _location_value(location.get("end"))
        description = str(feature.get("description") or feature_type or "UniProt feature")

        domains.append(
            {
                "name": description,
                "start_aa": start_aa,
                "end_aa": end_aa,
                "source": "uniprot",
                "evidence": feature_type or "feature",
                "sequence": "",
            }
        )

    return domains


def _location_value(value: Any) -> int | None:
    if isinstance(value, dict):
        return _safe_int(value.get("value"))
    return _safe_int(value)


def _request_json(
    url: str,
    params: dict[str, str],
    timeout_seconds: float,
) -> dict[str, Any]:
    payload = _request_text(url, params=params, timeout_seconds=timeout_seconds)
    try:
        return json.loads(payload)
    except json.JSONDecodeError as exc:
        raise UniProtError(f"UniProt returned invalid JSON for {url}.") from exc


def _request_text(
    url: str,
    *,
    params: dict[str, str] | None = None,
    timeout_seconds: float,
) -> str:
    request_url = url
    if params:
        request_url = f"{url}?{urlencode(params)}"

    request = Request(
        request_url,
        headers={"User-Agent": "bio-toolkit/0.1", "Accept": "application/json,text/plain"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return response.read().decode("utf-8")
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        raise UniProtError(f"UniProt request failed for {url}: {exc}") from exc


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _extract_comment_text(
    entry: dict[str, Any],
    allowed_types: set[str],
) -> list[str]:
    comments = []
    for comment in entry.get("comments", []):
        comment_type = str(comment.get("commentType") or "").upper()
        if comment_type not in allowed_types:
            continue

        texts = comment.get("texts", [])
        if texts:
            for item in texts:
                value = str(item.get("value") or "").strip()
                if value:
                    comments.append(value)
            continue

        reaction = comment.get("reaction", {})
        reaction_name = str(reaction.get("name") or "").strip()
        if reaction_name:
            comments.append(reaction_name)

        molecules = comment.get("molecule") or []
        for molecule in molecules if isinstance(molecules, list) else []:
            value = str(molecule.get("value") or "").strip()
            if value:
                comments.append(value)

        locations = comment.get("subcellularLocations", [])
        for location in locations:
            location_name = str(location.get("location", {}).get("value") or "").strip()
            if location_name:
                comments.append(location_name)

    return comments[:8]


def _extract_cross_references(entry: dict[str, Any]) -> list[dict[str, str]]:
    cross_references = []
    for item in entry.get("uniProtKBCrossReferences", []):
        database = str(item.get("database") or "").strip()
        identifier = str(item.get("id") or "").strip()
        if not database or not identifier:
            continue

        properties = []
        for property_item in item.get("properties", []):
            key = str(property_item.get("key") or "").strip()
            value = str(property_item.get("value") or "").strip()
            if key and value:
                properties.append(f"{key}: {value}")

        cross_references.append(
            {
                "database": database,
                "id": identifier,
                "properties": "; ".join(properties),
            }
        )

    return cross_references[:20]


def _sequence_preview(value: Any) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    return text[:80] + ("..." if len(text) > 80 else "")


def _protein_existence(entry: dict[str, Any]) -> str:
    protein_existence = entry.get("proteinExistence", {})
    if isinstance(protein_existence, dict):
        return str(protein_existence.get("value") or "-")
    return str(protein_existence or "-")


def _is_reviewed_entry(entry: dict[str, Any]) -> bool:
    entry_type = str(entry.get("entryType") or "").strip().lower()
    return "reviewed" in entry_type or "swiss-prot" in entry_type
