from bio_toolkit.config.settings import Settings, get_settings, refresh_settings


def test_settings_dataclass_and_refresh_exist() -> None:
    settings = refresh_settings()
    assert isinstance(settings, Settings)
    assert callable(get_settings)
