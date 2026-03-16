from pathlib import Path
import sys


def base_path() -> Path:
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parents[2]


def asset_path(*parts: str) -> str:
    return str(base_path().joinpath(*parts))
