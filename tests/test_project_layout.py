import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ProjectLayoutTests(unittest.TestCase):
    def test_preparation_artifacts_exist(self) -> None:
        expected_files = [
            ROOT / "README.md",
            ROOT / "pyproject.toml",
            ROOT / ".env.example",
            ROOT / ".gitignore",
            ROOT / ".planning" / "PROJECT.md",
            ROOT / ".planning" / "REQUIREMENTS.md",
            ROOT / ".planning" / "ROADMAP.md",
            ROOT / ".planning" / "STATE.md",
            ROOT / "docs" / "ARCHITECTURE.md",
            ROOT / "docs" / "CLI.md",
            ROOT / "docs" / "DEVELOPMENT.md",
            ROOT / "docs" / "FUNCTIONALITIES.md",
            ROOT / "src" / "bio_toolkit" / "analysis.py",
            ROOT / "src" / "bio_toolkit" / "annotations.py",
            ROOT / "src" / "bio_toolkit" / "__init__.py",
            ROOT / "src" / "bio_toolkit" / "cache_store.py",
            ROOT / "src" / "bio_toolkit" / "legacy_cli.py",
            ROOT / "src" / "bio_toolkit" / "legacy_config.py",
            ROOT / "src" / "bio_toolkit" / "legacy_providers.py",
            ROOT / "src" / "bio_toolkit" / "cli" / "__init__.py",
            ROOT / "src" / "bio_toolkit" / "config" / "__init__.py",
            ROOT / "src" / "bio_toolkit" / "providers" / "__init__.py",
            ROOT / "src" / "bio_toolkit" / "exporters.py",
            ROOT / "src" / "bio_toolkit" / "interactive_picker.py",
            ROOT / "src" / "bio_toolkit" / "ncbi.py",
            ROOT / "src" / "bio_toolkit" / "sequence_io.py",
            ROOT / "src" / "bio_toolkit" / "transforms.py",
        ]

        missing = [str(path.relative_to(ROOT)) for path in expected_files if not path.exists()]
        self.assertFalse(missing, f"Missing expected project files: {missing}")


if __name__ == "__main__":
    unittest.main()
