from __future__ import annotations

from pathlib import Path

from bio_toolkit.exporters import normalize_report_export_format


def human_int(value) -> str:
    if value in (None, "-"):
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    try:
        return f"{int(value):,}"
    except (TypeError, ValueError):
        return str(value)


def metric_value(value, *, suffix: str = "") -> str:
    if value in (None, "-"):
        return "-"
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}{suffix}"
    if isinstance(value, float):
        return f"{value:,.2f}{suffix}"
    return f"{value}{suffix}"


def preview_text(content: str, preview_lines: int) -> str:
    if preview_lines <= 0:
        return ""
    return "\n".join(content.splitlines()[:preview_lines])


def resolve_report_export_format(export_format: str, output: Path) -> str:
    normalized = export_format.strip().lower()
    if normalized == "auto":
        suffix = output.suffix.lower()
        if suffix in {".json", ".csv"}:
            return normalize_report_export_format(suffix[1:])
        return "json"
    return normalize_report_export_format(normalized)


def write_text_export(
    *,
    output: Path | None,
    default_output: Path,
    content: str,
) -> Path:
    destination = output or default_output
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(content, encoding="utf-8")
    return destination


def source_label(source_info: dict) -> str:
    label = str(source_info.get("label", "-"))
    kind = str(source_info.get("kind", "")).lower()
    if kind == "file":
        return Path(label).name
    return label


def transform_output_label(source_info: dict) -> str:
    label = str(source_info.get("label", "transformed"))
    kind = str(source_info.get("kind", "")).lower()
    if kind == "file":
        return Path(label).stem
    return label


def annotation_output_label(source_info: dict) -> str:
    label = str(source_info.get("label", "annotation"))
    kind = str(source_info.get("kind", "")).lower()
    if kind == "file":
        return Path(label).stem
    return label
