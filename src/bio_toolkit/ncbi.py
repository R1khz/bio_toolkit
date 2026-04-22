from __future__ import annotations

import csv
import json
import re
from dataclasses import asdict, dataclass
from io import StringIO
from pathlib import Path
from typing import Any
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from bio_toolkit.config import Settings

EUTILS_BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"
BLAST_BASE_URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"
SUPPORTED_DATABASES = {"nucleotide", "protein"}
SUPPORTED_RETTYPES = {"fasta": "fasta", "gb": "gb", "genbank": "gb"}
SUPPORTED_BLAST_PROGRAMS = {"blastn", "blastp", "blastx", "tblastn", "tblastx"}


class NcbiError(RuntimeError):
    """Raised when an NCBI request or response fails."""


class NcbiConfigurationError(NcbiError):
    """Raised when required NCBI runtime settings are missing."""


@dataclass(frozen=True)
class SearchResult:
    accession: str
    title: str
    organism: str
    source_db: str
    uid: str
    length: int | None = None
    provider: str = "ncbi"
    database: str = ""


@dataclass(frozen=True)
class FetchResult:
    accession: str
    database: str
    rettype: str
    content: str
    file_suffix: str
    source: str = "ncbi"
    provider: str = "ncbi"


@dataclass(frozen=True)
class BlastSubmission:
    rid: str
    rtoe_seconds: int
    program: str
    database: str
    hitlist_size: int
    expect: float


@dataclass(frozen=True)
class BlastSearchInfo:
    rid: str
    status: str
    there_are_hits: bool | None = None


@dataclass(frozen=True)
class BlastHit:
    query_id: str
    subject_id: str
    percent_identity: float
    alignment_length: int
    mismatches: int
    gap_opens: int
    query_start: int
    query_end: int
    subject_start: int
    subject_end: int
    e_value: str
    bit_score: float
    query_coverage: float | None = None


class NcbiClient:
    def __init__(
        self,
        *,
        email: str,
        tool_name: str = "bio-toolkit",
        api_key: str = "",
        timeout_seconds: float = 20.0,
    ) -> None:
        if not email:
            raise NcbiConfigurationError("NCBI_EMAIL is required before using NCBI commands.")

        self.email = email
        self.tool_name = tool_name
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds

    @classmethod
    def from_settings(cls, settings: Settings) -> NcbiClient:
        return cls(
            email=settings.ncbi_email,
            tool_name=settings.ncbi_tool_name,
            api_key=settings.ncbi_api_key,
        )

    def search(
        self,
        *,
        database: str,
        query: str,
        organism: str = "",
        limit: int = 10,
    ) -> list[SearchResult]:
        resolved_db = validate_database(database)
        resolved_limit = validate_limit(limit)
        term = build_search_term(query, organism)

        search_payload = self._request_json(
            "esearch.fcgi",
            {
                "db": resolved_db,
                "term": term,
                "retmax": str(resolved_limit),
                "retmode": "json",
                "idtype": "acc",
            },
        )

        id_list = search_payload.get("esearchresult", {}).get("idlist", [])
        if not id_list:
            return []

        summary_payload = self._request_json(
            "esummary.fcgi",
            {
                "db": resolved_db,
                "id": ",".join(id_list),
                "retmode": "json",
            },
        )

        return _parse_summary_results(summary_payload, database=resolved_db)

    def fetch(
        self,
        *,
        database: str,
        accession: str,
        rettype: str = "fasta",
    ) -> FetchResult:
        resolved_db = validate_database(database)
        resolved_rettype = normalize_rettype(rettype)
        content = self._request_text(
            "efetch.fcgi",
            {
                "db": resolved_db,
                "id": accession.strip(),
                "rettype": resolved_rettype,
                "retmode": "text",
            },
        )

        if not content.strip():
            raise NcbiError("NCBI returned an empty record.")

        return FetchResult(
            accession=accession.strip(),
            database=resolved_db,
            rettype=resolved_rettype,
            content=content,
            file_suffix=_suffix_for_rettype(resolved_rettype),
        )

    def blast_submit(
        self,
        *,
        program: str,
        database: str,
        query: str,
        hitlist_size: int = 10,
        expect: float = 10.0,
    ) -> BlastSubmission:
        resolved_program = validate_blast_program(program)
        resolved_hitlist_size = validate_positive_int(hitlist_size, field_name="hitlist_size")
        resolved_expect = validate_positive_float(expect, field_name="expect")
        clean_query = query.strip()
        if not clean_query:
            raise ValueError("BLAST query cannot be empty.")
        if not database.strip():
            raise ValueError("BLAST database cannot be empty.")

        payload = self._request_text_absolute(
            BLAST_BASE_URL,
            {
                "CMD": "Put",
                "PROGRAM": resolved_program,
                "DATABASE": database.strip(),
                "QUERY": clean_query,
                "HITLIST_SIZE": str(resolved_hitlist_size),
                "EXPECT": str(resolved_expect),
                "FORMAT_TYPE": "CSV",
                "ALIGNMENT_VIEW": "Tabular",
            },
            method="POST",
        )

        rid = _extract_blast_value(payload, "RID")
        if rid is None:
            raise NcbiError("BLAST submission did not return a RID.")

        rtoe_raw = _extract_blast_value(payload, "RTOE")
        rtoe_seconds = _safe_int(rtoe_raw) or 0

        return BlastSubmission(
            rid=rid,
            rtoe_seconds=rtoe_seconds,
            program=resolved_program,
            database=database.strip(),
            hitlist_size=resolved_hitlist_size,
            expect=resolved_expect,
        )

    def blast_check_status(self, *, rid: str) -> BlastSearchInfo:
        clean_rid = rid.strip()
        if not clean_rid:
            raise ValueError("RID cannot be empty.")

        payload = self._request_text_absolute(
            BLAST_BASE_URL,
            {
                "CMD": "Get",
                "RID": clean_rid,
                "FORMAT_OBJECT": "SearchInfo",
            },
        )

        status = _extract_blast_value(payload, "Status")
        if status is None:
            raise NcbiError("BLAST status response did not include a status.")

        there_are_hits_value = _extract_blast_value(payload, "ThereAreHits")
        there_are_hits = _parse_yes_no(there_are_hits_value)

        return BlastSearchInfo(
            rid=clean_rid,
            status=status.upper(),
            there_are_hits=there_are_hits,
        )

    def blast_fetch_results(self, *, rid: str) -> list[BlastHit]:
        clean_rid = rid.strip()
        if not clean_rid:
            raise ValueError("RID cannot be empty.")

        payload = self._request_text_absolute(
            BLAST_BASE_URL,
            {
                "CMD": "Get",
                "RID": clean_rid,
                "FORMAT_TYPE": "CSV",
                "ALIGNMENT_VIEW": "Tabular",
            },
        )
        return parse_blast_tabular_csv(payload)

    def _request_json(self, endpoint: str, params: dict[str, str]) -> dict[str, Any]:
        raw_response = self._request_text(endpoint, params)
        try:
            return json.loads(raw_response)
        except json.JSONDecodeError as exc:
            raise NcbiError(f"NCBI returned invalid JSON for {endpoint}.") from exc

    def _request_text(self, endpoint: str, params: dict[str, str]) -> str:
        request_url = build_request_url(endpoint, self._base_params() | params)
        return self._request_text_absolute(request_url, {}, already_encoded=True)

    def _request_text_absolute(
        self,
        url: str,
        params: dict[str, str],
        *,
        method: str = "GET",
        already_encoded: bool = False,
    ) -> str:
        request_url = url
        request_data = None
        normalized_method = method.strip().upper()

        if not already_encoded:
            if normalized_method == "POST":
                request_data = urlencode(self._base_params() | params).encode("utf-8")
            else:
                request_url = f"{url}?{urlencode(self._base_params() | params)}"

        request = Request(
            request_url,
            data=request_data,
            method=normalized_method,
            headers={"User-Agent": f"{self.tool_name}/0.1 (+{self.email})"},
        )

        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                payload = response.read().decode("utf-8")
        except Exception as exc:  # pragma: no cover - depends on network/runtime
            raise NcbiError(f"NCBI request failed for {url}: {exc}") from exc

        return payload

    def _base_params(self) -> dict[str, str]:
        params = {"tool": self.tool_name, "email": self.email}
        if self.api_key:
            params["api_key"] = self.api_key
        return params


def build_request_url(endpoint: str, params: dict[str, str]) -> str:
    return f"{EUTILS_BASE_URL}/{endpoint}?{urlencode(params)}"


def build_search_term(query: str, organism: str = "") -> str:
    clean_query = query.strip()
    if not clean_query:
        raise ValueError("Query cannot be empty.")

    if not organism.strip():
        return clean_query

    return f"({clean_query}) AND ({organism.strip()}[Organism])"


def default_fetch_path(output_dir: Path, accession: str, rettype: str) -> Path:
    normalized_rettype = normalize_rettype(rettype)
    return output_dir / f"{accession.strip()}{_suffix_for_rettype(normalized_rettype)}"


def search_results_to_dict(results: list[SearchResult]) -> list[dict[str, Any]]:
    return [asdict(item) for item in results]


def blast_hits_to_dict(results: list[BlastHit]) -> list[dict[str, Any]]:
    return [asdict(item) for item in results]


def parse_blast_tabular_csv(payload: str) -> list[BlastHit]:
    cleaned_lines = [
        line.strip()
        for line in payload.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    if not cleaned_lines:
        return []

    reader = csv.reader(StringIO("\n".join(cleaned_lines)))
    hits: list[BlastHit] = []

    for row in reader:
        if len(row) not in {12, 13}:
            raise NcbiError(
                "BLAST returned an unexpected CSV row format. Expected 12 or 13 columns."
            )
        hits.append(_blast_csv_row_to_hit(row))

    return hits


def _parse_summary_results(payload: dict[str, Any], *, database: str) -> list[SearchResult]:
    result_section = payload.get("result", {})
    ordered_uids = result_section.get("uids", [])
    parsed_results: list[SearchResult] = []

    for uid in ordered_uids:
        raw_summary = result_section.get(str(uid), {})
        if not raw_summary:
            continue
        parsed_results.append(_summary_to_result(raw_summary, database=database))

    return parsed_results


def _summary_to_result(summary: dict[str, Any], *, database: str) -> SearchResult:
    accession = _first_present(summary, ("caption", "accessionversion", "extra", "uid"))
    title = str(_first_present(summary, ("title",)) or "-")
    organism = str(_first_present(summary, ("organism",)) or _organism_from_title(title) or "-")
    source_db = str(_first_present(summary, ("sourcedb", "source", "subtype")) or database)
    length = _safe_int(_first_present(summary, ("slen", "length")))

    return SearchResult(
        accession=_accession_from_value(str(accession or summary.get("uid", "-"))),
        title=title,
        organism=organism,
        source_db=source_db,
        uid=str(summary.get("uid", "")),
        length=length,
        provider="ncbi",
        database=database,
    )


def _first_present(summary: dict[str, Any], keys: tuple[str, ...]) -> Any:
    for key in keys:
        if key in summary and summary[key] not in (None, ""):
            return summary[key]
    return None


def _organism_from_title(title: str) -> str | None:
    match = re.search(r"\[([^\[\]]+)\]\s*$", title)
    if match:
        return match.group(1)
    return None


def _accession_from_value(value: str) -> str:
    if "|" not in value:
        return value

    parts = [part for part in value.split("|") if part]
    for index, part in enumerate(parts):
        if part in {"ref", "gb", "emb", "dbj"} and index + 1 < len(parts):
            return parts[index + 1]
    return parts[-1]


def validate_database(database: str) -> str:
    resolved = database.strip().lower()
    if resolved not in SUPPORTED_DATABASES:
        allowed = ", ".join(sorted(SUPPORTED_DATABASES))
        raise ValueError(f"Unsupported database '{database}'. Use one of: {allowed}.")
    return resolved


def validate_limit(limit: int) -> int:
    if limit < 1:
        raise ValueError("Limit must be at least 1.")
    if limit > 100:
        raise ValueError("Limit must be 100 or less for interactive search.")
    return limit


def normalize_rettype(rettype: str) -> str:
    resolved = rettype.strip().lower()
    if resolved not in SUPPORTED_RETTYPES:
        allowed = ", ".join(sorted(SUPPORTED_RETTYPES))
        raise ValueError(f"Unsupported rettype '{rettype}'. Use one of: {allowed}.")
    return SUPPORTED_RETTYPES[resolved]


def validate_blast_program(program: str) -> str:
    resolved = program.strip().lower()
    if resolved not in SUPPORTED_BLAST_PROGRAMS:
        allowed = ", ".join(sorted(SUPPORTED_BLAST_PROGRAMS))
        raise ValueError(f"Unsupported BLAST program '{program}'. Use one of: {allowed}.")
    return resolved


def validate_positive_int(value: int, *, field_name: str) -> int:
    if value < 1:
        raise ValueError(f"{field_name} must be at least 1.")
    return value


def validate_positive_float(value: float, *, field_name: str) -> float:
    if value <= 0:
        raise ValueError(f"{field_name} must be greater than 0.")
    return value


def _suffix_for_rettype(rettype: str) -> str:
    return ".fasta" if rettype == "fasta" else ".gb"


def _extract_blast_value(payload: str, key: str) -> str | None:
    match = re.search(rf"{re.escape(key)}\s*=\s*([^\s<]+)", payload, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def _parse_yes_no(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized == "yes":
        return True
    if normalized == "no":
        return False
    return None


def _blast_csv_row_to_hit(row: list[str]) -> BlastHit:
    query_coverage = float(row[12]) if len(row) == 13 and row[12] else None
    return BlastHit(
        query_id=row[0],
        subject_id=row[1],
        percent_identity=float(row[2]),
        alignment_length=int(row[3]),
        mismatches=int(row[4]),
        gap_opens=int(row[5]),
        query_start=int(row[6]),
        query_end=int(row[7]),
        subject_start=int(row[8]),
        subject_end=int(row[9]),
        e_value=row[10],
        bit_score=float(row[11]),
        query_coverage=query_coverage,
    )


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
