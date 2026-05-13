from __future__ import annotations

import json
from typing import Any
from urllib.parse import quote
from urllib.request import Request, urlopen

ALPHAFOLD_API_BASE_URL = "https://alphafold.ebi.ac.uk/api/prediction"
ALPHAFOLD_ENTRY_BASE_URL = "https://alphafold.ebi.ac.uk/entry"


class AlphaFoldError(RuntimeError):
    """Raised when AlphaFold DB metadata could not be retrieved."""


def fetch_alphafold_prediction(
    accession: str,
    *,
    timeout_seconds: float = 20.0,
) -> dict[str, Any] | None:
    clean_accession = accession.strip()
    if not clean_accession:
        raise ValueError("AlphaFold lookup accession cannot be empty.")

    payload = _request_json(
        f"{ALPHAFOLD_API_BASE_URL}/{quote(clean_accession)}",
        timeout_seconds=timeout_seconds,
    )
    if isinstance(payload, list):
        if not payload:
            return None
        item = payload[0]
    elif isinstance(payload, dict):
        item = payload
    else:
        return None

    model_id = _first_present(item, ("modelEntityId", "entryId", "modelId"))
    model_label = str(model_id or clean_accession)

    return {
        "accession": str(_first_present(item, ("uniprotAccession",)) or clean_accession),
        "model_id": model_label,
        "entry_url": f"{ALPHAFOLD_ENTRY_BASE_URL}/{model_label}",
        "sequence_start": _first_present(item, ("sequenceStart", "uniprotStart")),
        "sequence_end": _first_present(item, ("sequenceEnd", "uniprotEnd")),
        "avg_plddt": _safe_float(
            _first_present(
                item,
                (
                    "confidenceAvgLocalScore",
                    "avgPlddt",
                    "avg_plddt",
                    "globalMetricValue",
                ),
            )
        ),
        "is_reviewed": _first_present(item, ("isUniProtReviewed", "isReviewed")),
        "is_reference_proteome": _first_present(
            item,
            ("isUniProtReferenceProteome", "isReferenceProteome"),
        ),
        "latest_version": _first_present(item, ("latestVersion", "version")),
        "created_date": _first_present(item, ("modelCreatedDate", "createdDate")),
    }


def _request_json(url: str, *, timeout_seconds: float) -> Any:
    request = Request(
        url,
        headers={"User-Agent": "bio-toolkit/0.1", "Accept": "application/json"},
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as exc:  # pragma: no cover - network/runtime dependent
        message = str(exc)
        if "HTTP Error 404" in message:
            return None
        if "HTTP Error 400" in message:
            raise AlphaFoldError(
                "AlphaFold rejected the request — the accession may not exist "
                "in the AlphaFold DB or is not a valid UniProt accession."
            ) from exc
        raise AlphaFoldError(f"AlphaFold request failed for {url}: {exc}") from exc


def _first_present(payload: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in payload and payload[key] not in (None, ""):
            return payload[key]
    return None


def _safe_float(value: Any) -> float | None:
    try:
        return round(float(value), 2)
    except (TypeError, ValueError):
        return None
