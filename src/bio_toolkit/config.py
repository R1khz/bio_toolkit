from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for bare environments

    def load_dotenv(*_args, **_kwargs) -> bool:
        return False


def _resolve_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() not in {"0", "false", "no", "off"}


def _resolve_str(name: str, default: str) -> str:
    raw = os.getenv(name)
    if raw is None:
        return default
    stripped = raw.strip()
    return stripped or default


def _resolve_path(name: str, default: Path, runtime_root: Path) -> Path:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    path = Path(raw.strip()).expanduser()
    if not path.is_absolute():
        path = runtime_root / path
    return path


@dataclass(frozen=True)
class InstallationInfo:
    package_root: Path
    import_root: Path
    active_repo_root: Path | None
    runtime_root: Path
    install_mode: str
    active_repo_matches_import: bool | None


@dataclass(frozen=True)
class Settings:
    ncbi_email: str
    ncbi_api_key: str
    ncbi_tool_name: str
    cache_dir: Path
    output_dir: Path
    color_enabled: bool
    runtime_root: Path
    env_file: Path
    env_file_found: bool


def get_package_root() -> Path:
    return Path(__file__).resolve().parent


def _looks_like_project_root(path: Path) -> bool:
    return (path / "pyproject.toml").exists() and (
        path / "src" / "bio_toolkit" / "__init__.py"
    ).exists()


def get_import_root() -> Path:
    package_root = get_package_root()
    editable_root = package_root.parent.parent if package_root.parent.name == "src" else None
    if editable_root is not None and _looks_like_project_root(editable_root):
        return editable_root
    return package_root.parent


def get_project_root() -> Path:
    return get_import_root()


def find_active_repo_root(start: Path | None = None) -> Path | None:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if _looks_like_project_root(candidate):
            return candidate
    return None


def get_runtime_root(start: Path | None = None) -> Path:
    return find_active_repo_root(start) or (start or Path.cwd()).resolve()


def get_installation_info(start: Path | None = None) -> InstallationInfo:
    package_root = get_package_root()
    import_root = get_import_root()
    active_repo_root = find_active_repo_root(start)
    runtime_root = active_repo_root or (start or Path.cwd()).resolve()

    if package_root == import_root / "src" / "bio_toolkit":
        install_mode = "editable"
    elif "site-packages" in package_root.parts:
        install_mode = "site-packages"
    else:
        install_mode = "direct"

    active_repo_matches_import = None
    if active_repo_root is not None:
        active_repo_matches_import = active_repo_root == import_root

    return InstallationInfo(
        package_root=package_root,
        import_root=import_root,
        active_repo_root=active_repo_root,
        runtime_root=runtime_root,
        install_mode=install_mode,
        active_repo_matches_import=active_repo_matches_import,
    )


def load_environment() -> tuple[Path, Path]:
    runtime_root = get_runtime_root()
    env_file = runtime_root / ".env"
    load_dotenv(env_file, override=False)
    return env_file, runtime_root


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env_file, runtime_root = load_environment()
    cache_dir = _resolve_path(
        "BIO_TOOLKIT_CACHE_DIR",
        Path.home() / ".cache" / "bio-toolkit",
        runtime_root,
    )
    output_dir = _resolve_path(
        "BIO_TOOLKIT_OUTPUT_DIR",
        runtime_root / "outputs",
        runtime_root,
    )

    return Settings(
        ncbi_email=_resolve_str("NCBI_EMAIL", ""),
        ncbi_api_key=_resolve_str("NCBI_API_KEY", ""),
        ncbi_tool_name=_resolve_str("NCBI_TOOL_NAME", "bio-toolkit"),
        cache_dir=cache_dir,
        output_dir=output_dir,
        color_enabled=_resolve_bool("BIO_TOOLKIT_COLOR", True),
        runtime_root=runtime_root,
        env_file=env_file,
        env_file_found=env_file.exists(),
    )


def refresh_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


def ensure_runtime_dirs(settings: Settings) -> None:
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
