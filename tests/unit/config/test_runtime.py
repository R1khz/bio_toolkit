from pathlib import Path

from bio_toolkit.config.runtime import get_runtime_root


def test_runtime_root_falls_back_to_current_directory(tmp_path: Path) -> None:
    root = get_runtime_root(tmp_path)
    assert root == tmp_path
