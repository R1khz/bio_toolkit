import importlib
import sys

import bio_toolkit.config as public_config
import bio_toolkit.config.settings as settings_module
from bio_toolkit.config.settings import Settings, get_settings, refresh_settings


def test_settings_dataclass_and_refresh_exist() -> None:
    settings = refresh_settings()
    assert isinstance(settings, Settings)
    assert callable(get_settings)


def test_config_imports_without_python_dotenv(monkeypatch) -> None:
    with monkeypatch.context() as patch:
        patch.setitem(sys.modules, "dotenv", None)

        reloaded_settings = importlib.reload(settings_module)
        reloaded_public = importlib.reload(public_config)

    importlib.reload(settings_module)
    importlib.reload(public_config)

    assert callable(reloaded_settings.load_dotenv)
    assert reloaded_public.get_settings is reloaded_settings.get_settings
