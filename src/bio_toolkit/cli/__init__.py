import sys
from types import ModuleType

from bio_toolkit import legacy_cli as _legacy_cli

from .app import app


class _LegacyCliPackage(ModuleType):
    def __getattr__(self, name: str):
        return getattr(_legacy_cli, name)

    def __setattr__(self, name: str, value) -> None:
        super().__setattr__(name, value)
        if hasattr(_legacy_cli, name):
            setattr(_legacy_cli, name, value)


sys.modules[__name__].__class__ = _LegacyCliPackage

__all__ = ["app"]
