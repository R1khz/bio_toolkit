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

    seq_start = _first_present(item, ("uniprotStart", "sequenceStart"))
    seq_end = _first_present(item, ("uniprotEnd", "sequenceEnd"))
    seq_length = (
        (seq_end - seq_start + 1)
        if isinstance(seq_start, int) and isinstance(seq_end, int)
        else None
    )

    plddt_very_high = _safe_float(_first_present(item, ("fractionPlddtVeryHigh",)))
    plddt_confident = _safe_float(_first_present(item, ("fractionPlddtConfident",)))
    plddt_low = _safe_float(_first_present(item, ("fractionPlddtLow",)))
    plddt_very_low = _safe_float(_first_present(item, ("fractionPlddtVeryLow",)))

    result: dict[str, Any] = {
        "accession": str(_first_present(item, ("uniprotAccession",)) or clean_accession),
        "entry_id": str(_first_present(item, ("entryId", "modelEntityId")) or model_label),
        "entry_url": f"{ALPHAFOLD_ENTRY_BASE_URL}/{model_label}",
        "gene": _first_present(item, ("gene",)),
        "uniprot_id": _first_present(item, ("uniprotId",)),
        "description": _first_present(item, ("uniprotDescription",)),
        "organism": _first_present(item, ("organismScientificName", "scientificName")),
        "sequence_length": seq_length,
        "avg_plddt": _safe_float(
            _first_present(
                item,
                ("confidenceAvgLocalScore", "avgPlddt", "avg_plddt", "globalMetricValue"),
            )
        ),
        "is_reviewed": _first_present(item, ("isUniProtReviewed", "isReviewed")),
        "latest_version": _first_present(item, ("latestVersion", "version")),
        "created_date": _first_present(item, ("modelCreatedDate", "createdDate")),
        "tool": _first_present(item, ("toolUsed",)),
        "pdb_url": _first_present(item, ("pdbUrl",)),
        "cif_url": _first_present(item, ("cifUrl",)),
    }
    if plddt_very_high is not None:
        result["plddt_very_high_pct"] = round(plddt_very_high * 100, 1)
    if plddt_confident is not None:
        result["plddt_confident_pct"] = round(plddt_confident * 100, 1)
    if plddt_low is not None:
        result["plddt_low_pct"] = round(plddt_low * 100, 1)
    if plddt_very_low is not None:
        result["plddt_very_low_pct"] = round(plddt_very_low * 100, 1)
    return result


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
