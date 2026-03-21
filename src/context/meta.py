from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


APP_NAME = "ContExt"


def _discover_version() -> str:
    try:
        return version("context")
    except PackageNotFoundError:
        return "0.1.0"


APP_VERSION = _discover_version()


__all__ = ["APP_NAME", "APP_VERSION"]
