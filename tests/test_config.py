import importlib.util
import os
import sys
import tempfile
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
CONFIG_FILE = ROOT / "src" / "bio_toolkit" / "config.py"


def _load_config_module():
    spec = importlib.util.spec_from_file_location("bio_toolkit_config", CONFIG_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ConfigTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = _load_config_module()
        self.original_env = os.environ.copy()

    def tearDown(self) -> None:
        os.environ.clear()
        os.environ.update(self.original_env)
        self.config.get_settings.cache_clear()

    def test_settings_respect_environment(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            cache_dir = tmp_path / "cache"
            output_dir = tmp_path / "outputs"

            os.environ["NCBI_EMAIL"] = "user@example.com"
            os.environ["NCBI_API_KEY"] = "secret"
            os.environ["NCBI_TOOL_NAME"] = "bio-toolkit-test"
            os.environ["BIO_TOOLKIT_CACHE_DIR"] = str(cache_dir)
            os.environ["BIO_TOOLKIT_OUTPUT_DIR"] = str(output_dir)
            os.environ["BIO_TOOLKIT_COLOR"] = "false"

            self.config.refresh_settings()
            settings = self.config.get_settings()

            self.assertEqual(settings.ncbi_email, "user@example.com")
            self.assertEqual(settings.ncbi_api_key, "secret")
            self.assertEqual(settings.ncbi_tool_name, "bio-toolkit-test")
            self.assertEqual(settings.cache_dir, cache_dir)
            self.assertEqual(settings.output_dir, output_dir)
            self.assertFalse(settings.color_enabled)

    def test_ensure_runtime_dirs_creates_missing_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            cache_dir = tmp_path / "cache"
            output_dir = tmp_path / "outputs"

            os.environ["BIO_TOOLKIT_CACHE_DIR"] = str(cache_dir)
            os.environ["BIO_TOOLKIT_OUTPUT_DIR"] = str(output_dir)

            settings = self.config.refresh_settings()
            self.config.ensure_runtime_dirs(settings)

            self.assertTrue(cache_dir.exists())
            self.assertTrue(output_dir.exists())

    def test_empty_path_values_fall_back_to_defaults(self) -> None:
        os.environ["NCBI_EMAIL"] = "user@example.com"
        os.environ["BIO_TOOLKIT_CACHE_DIR"] = "   "
        os.environ["BIO_TOOLKIT_OUTPUT_DIR"] = ""

        settings = self.config.refresh_settings()

        self.assertEqual(settings.cache_dir, Path.home() / ".cache" / "bio-toolkit")
        self.assertEqual(settings.output_dir, Path.cwd() / "outputs")

    def test_relative_paths_resolve_from_project_root(self) -> None:
        os.environ["NCBI_EMAIL"] = "user@example.com"
        os.environ["BIO_TOOLKIT_CACHE_DIR"] = ".cache/bio-toolkit"
        os.environ["BIO_TOOLKIT_OUTPUT_DIR"] = "outputs"

        settings = self.config.refresh_settings()

        self.assertEqual(settings.cache_dir, ROOT / ".cache" / "bio-toolkit")
        self.assertEqual(settings.output_dir, ROOT / "outputs")


if __name__ == "__main__":
    unittest.main()
