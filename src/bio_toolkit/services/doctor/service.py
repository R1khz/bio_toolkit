from __future__ import annotations

import platform
import sys
from pathlib import Path

from bio_toolkit.config import ensure_runtime_dirs, get_installation_info, refresh_settings
from bio_toolkit.contracts.doctor.models import DiagnosticRow

from .request import DoctorRequest
from .response import DoctorResponse


def run_doctor(request: DoctorRequest) -> DoctorResponse:
    settings = refresh_settings()
    if request.create_dirs:
        ensure_runtime_dirs(settings)
        settings = refresh_settings()

    installation = get_installation_info()
    rows = [
        DiagnosticRow(
            setting="NCBI_EMAIL",
            value=settings.ncbi_email or "-",
            status="configured" if settings.ncbi_email else "missing",
        ),
        DiagnosticRow(
            setting="NCBI_API_KEY",
            value=_mask(settings.ncbi_api_key),
            status="configured" if settings.ncbi_api_key else "optional",
        ),
        DiagnosticRow(
            setting="NCBI_TOOL_NAME",
            value=settings.ncbi_tool_name,
            status="configured",
        ),
        DiagnosticRow(
            setting="ENV_FILE",
            value=str(settings.env_file),
            status=_env_status(settings.env_file),
        ),
        DiagnosticRow(
            setting="RUNTIME_ROOT",
            value=str(settings.runtime_root),
            status="detected",
        ),
        DiagnosticRow(
            setting="PACKAGE_ROOT",
            value=str(installation.package_root),
            status="detected",
        ),
        DiagnosticRow(
            setting="INSTALL_MODE",
            value=installation.install_mode,
            status="detected",
        ),
    ]
    if installation.active_repo_root is not None:
        rows.append(
            DiagnosticRow(
                setting="ACTIVE_REPO",
                value=str(installation.active_repo_root),
                status=_active_repo_status(installation.active_repo_matches_import),
            )
        )

    rows.extend(
        [
            DiagnosticRow(
                setting="PLATFORM",
                value=platform.system().lower(),
                status="supported" if platform.system().lower() == "linux" else "untested",
            ),
            DiagnosticRow(
                setting="PYTHON",
                value=sys.version.split()[0],
                status="detected",
            ),
            DiagnosticRow(
                setting="CACHE_DIR",
                value=str(settings.cache_dir),
                status=_path_status(settings.cache_dir),
            ),
            DiagnosticRow(
                setting="OUTPUT_DIR",
                value=str(settings.output_dir),
                status=_path_status(settings.output_dir),
            ),
            DiagnosticRow(
                setting="COLOR",
                value=str(settings.color_enabled).lower(),
                status="configured",
            ),
        ]
    )

    warnings = []
    if not settings.ncbi_email:
        warnings.append(
            "NCBI_EMAIL is not set. Add it in `.env` or export it before using NCBI commands."
        )
    if installation.active_repo_matches_import is False:
        warnings.extend(
            [
                "Bio Toolkit is being imported from a different clone than the active repository.",
                f"Imported package root: {installation.package_root}",
                f"Active repository: {installation.active_repo_root}",
                (
                    "Reinstall this clone with `./.venv/bin/python -m pip install -e "
                    '"[dev]"` to realign the environment.'
                ),
            ]
        )

    return DoctorResponse(rows=rows, warnings=warnings)


def _mask(value: str) -> str:
    if not value:
        return "-"
    if len(value) <= 4:
        return "*" * len(value)
    return f"{value[:2]}{'*' * (len(value) - 4)}{value[-2:]}"


def _env_status(env_file: Path) -> str:
    return "present" if env_file.exists() else "missing"


def _active_repo_status(active_repo_matches_import: bool | None) -> str:
    if active_repo_matches_import is None:
        return "unknown"
    return "aligned" if active_repo_matches_import else "mismatch"


def _path_status(path: Path) -> str:
    return "present" if path.exists() else "missing"
