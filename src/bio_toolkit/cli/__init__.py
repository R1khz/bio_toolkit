import sys
from types import ModuleType

from bio_toolkit import legacy_cli as _legacy_cli

from .app import app

_PACKAGE_INTERNAL_NAMES = {
    "ModuleType",
    "_LegacyCliPackage",
    "_PACKAGE_INTERNAL_NAMES",
    "_FORWARDED_NAMES",
    "_legacy_cli",
    "app",
    "sys",
}
_FORWARDED_NAMES = set()

for _name, _value in vars(_legacy_cli).items():
    if _name.startswith("__") and _name.endswith("__"):
        continue
    if _name in _PACKAGE_INTERNAL_NAMES:
        continue
    globals()[_name] = _value
    _FORWARDED_NAMES.add(_name)


class _LegacyCliPackage(ModuleType):
    def __setattr__(self, name: str, value) -> None:
        super().__setattr__(name, value)
        if name in _FORWARDED_NAMES:
            setattr(_legacy_cli, name, value)


sys.modules[__name__].__class__ = _LegacyCliPackage

__all__ = ["app"]
