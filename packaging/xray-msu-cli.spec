# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller: однофайловый CLI (Linux: dist/xray-msu-cli; Windows: xray-msu-cli.exe). См. xray-msu-gui.spec, build-ubuntu.sh, build-windows.ps1."""
import os
from pathlib import Path

_env = os.environ.get("PYINSTALLER_SPEC_ROOT")
ROOT = Path(_env).resolve() if _env else Path(os.getcwd()).resolve()

block_cipher = None

datas = [
    (str(ROOT / "data" / "f0_WaasKirf.dat"), "data"),
    (str(ROOT / "config"), "config"),
]

hiddenimports = [
    "src",
    "src.runtime_layout",
    "src.model.atom.atom",
    "src.model.crystal.crystal",
    "src.model.crystal.structure",
    "src.model.crystal.utils",
    "src.model.group.space",
    "src.model.pattern.powder",
    "src.model.pattern.plot",
    "src.model.pattern.utils",
]
hiddenimports += [
    "spglib",
    "yaml",
    "omegaconf",
    "matplotlib.backends.backend_agg",
    "PIL",
    "scipy",
    "scipy.special",
    "scipy._lib",
    "kiwisolver",
    "contourpy",
    "dateutil",
    "pyparsing",
    "cycler",
    "fontTools",
    "fontTools.misc",
]

a = Analysis(
    [str(ROOT / "entry_cli.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "PyQt5",
        "PyQt6",
        "PySide2",
        "PySide6",
        "gtk",
        "gi",
        "torch",
        "torchaudio",
        "torchvision",
        "tensorflow",
        "cupy",
        "IPython",
        "jupyter",
        "transformers",
        "nvidia",
        "triton",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="xray-msu-cli",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
