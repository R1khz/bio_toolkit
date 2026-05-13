import subprocess
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class InstallationSmokeTests(unittest.TestCase):
    def test_python_module_entrypoint_runs_from_current_clone(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "bio_toolkit", "--help"],
            capture_output=True,
            check=False,
            cwd=ROOT,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertIn("doctor", result.stdout)
        self.assertIn("search", result.stdout)

    def test_imported_package_resolves_to_current_clone(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                (
                    "from pathlib import Path; import bio_toolkit; "
                    "print(Path(bio_toolkit.__file__).resolve())"
                ),
            ],
            capture_output=True,
            check=False,
            cwd=ROOT,
            text=True,
        )

        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)
        self.assertEqual(
            Path(result.stdout.strip()),
            ROOT / "src" / "bio_toolkit" / "__init__.py",
        )

    def test_project_scripts_expose_short_btk_alias(self) -> None:
        pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        scripts = pyproject["project"]["scripts"]

        self.assertEqual(scripts["bio-toolkit"], "bio_toolkit.cli:app")
        self.assertEqual(scripts["btk"], "bio_toolkit.cli:app")


if __name__ == "__main__":
    unittest.main()
