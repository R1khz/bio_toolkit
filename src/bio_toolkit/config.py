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


def _resolve_path(name: str, default: Path) -> Path:
    raw = os.getenv(name)
    if raw is None or not raw.strip():
        return default

    path = Path(raw.strip()).expanduser()
    if not path.is_absolute():
        path = get_project_root() / path
    return path


@dataclass(frozen=True)
class Settings:
    ncbi_email: str
    ncbi_api_key: str
    ncbi_tool_name: str
    cache_dir: Path
    output_dir: Path
    color_enabled: bool
    env_file: Path
    env_file_found: bool


def get_project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_environment() -> Path:
    env_file = get_project_root() / ".env"
    load_dotenv(env_file, override=False)
    return env_file


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    env_file = load_environment()
    cache_dir = _resolve_path("BIO_TOOLKIT_CACHE_DIR", Path.home() / ".cache" / "bio-toolkit")
    output_dir = _resolve_path("BIO_TOOLKIT_OUTPUT_DIR", Path.cwd() / "outputs")

    return Settings(
        ncbi_email=_resolve_str("NCBI_EMAIL", ""),
        ncbi_api_key=_resolve_str("NCBI_API_KEY", ""),
        ncbi_tool_name=_resolve_str("NCBI_TOOL_NAME", "bio-toolkit"),
        cache_dir=cache_dir,
        output_dir=output_dir,
        color_enabled=_resolve_bool("BIO_TOOLKIT_COLOR", True),
        env_file=env_file,
        env_file_found=env_file.exists(),
    )


def refresh_settings() -> Settings:
    get_settings.cache_clear()
    return get_settings()


def ensure_runtime_dirs(settings: Settings) -> None:
    settings.cache_dir.mkdir(parents=True, exist_ok=True)
    settings.output_dir.mkdir(parents=True, exist_ok=True)
