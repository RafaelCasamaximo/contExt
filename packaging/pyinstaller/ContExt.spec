# -*- mode: python ; coding: utf-8 -*-

import os
from pathlib import Path
import sys

from PyInstaller.utils.hooks import collect_submodules


PROJECT_ROOT = Path(SPECPATH).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
MAIN_SCRIPT = PROJECT_ROOT / "main.py"
WINDOWS_ICON = PROJECT_ROOT / "icons" / "Icon.ico"
MACOS_ICON = PROJECT_ROOT / "icons" / "Icon.png"

datas = [
    (str(PROJECT_ROOT / "icons"), "icons"),
    (str(PROJECT_ROOT / "fonts"), "fonts"),
    (str(PROJECT_ROOT / "src" / "context" / "ui" / "translations.json"), "context/ui"),
]

hiddenimports = collect_submodules("pydicom")

a = Analysis(
    [str(MAIN_SCRIPT)],
    pathex=[str(SRC_ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

if sys.platform == "darwin":
    target_arch = os.environ.get("CONTEXT_TARGET_ARCH")
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="ContExt",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=str(MACOS_ICON),
        target_arch=target_arch,
    )

    coll = COLLECT(
        exe,
        a.binaries,
        a.datas,
        strip=False,
        upx=False,
        name="ContExt",
    )

    app = BUNDLE(
        coll,
        name="ContExt.app",
        icon=str(MACOS_ICON),
        bundle_identifier="com.rafaelcasamaximo.context",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.datas,
        [],
        name="ContExt",
        debug=False,
        bootloader_ignore_signals=False,
        strip=False,
        upx=False,
        console=False,
        icon=str(WINDOWS_ICON),
    )
