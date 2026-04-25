from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class InstallationInfo:
    package_root: Path
    import_root: Path
    active_repo_root: Path | None
    runtime_root: Path
    install_mode: str
    active_repo_matches_import: bool | None


def get_package_root() -> Path:
    return Path(__file__).resolve().parents[1]


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
