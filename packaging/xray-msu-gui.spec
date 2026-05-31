# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller: GUI. Windows/macOS — один exe; Linux — onedir (dist/xray-msu-gui/xray-msu-gui + _internal/), иначе Tcl/Tk .so в onefile часто не грузятся.

   Ubuntu: ./packaging/build-ubuntu.sh
   Windows: packaging\\build-windows.ps1 / .bat
"""
import os
import re
import subprocess
import sys
from pathlib import Path

from PyInstaller.building.datastruct import normalize_toc
from PyInstaller.depend import bindepend
from PyInstaller.utils.hooks.tcl_tk import tcltk_info

_env = os.environ.get("PYINSTALLER_SPEC_ROOT")
ROOT = Path(_env).resolve() if _env else Path(os.getcwd()).resolve()


def _linux_tcl_tk_binaries():
    """Пакуем Tcl/Tk .so в onefile: tcltk_info иногда не находит пары для Tcl 9; тогда libtcl9.0.so не попадает в сборку."""
    if not sys.platform.startswith("linux"):
        return []
    try:
        import _tkinter

        tk_so = getattr(_tkinter, "__file__", None)
        if not tk_so or not Path(tk_so).is_file():
            return []
    except Exception:
        return []

    try:
        seeds = []
        seen = set()

        def add_binary(src_path):
            src_resolved = str(Path(src_path).resolve())
            if src_resolved in seen:
                return
            seen.add(src_resolved)
            seeds.append((Path(src_resolved).name, src_resolved, "BINARY"))

        if getattr(tcltk_info, "available", False):
            for p in (tcltk_info.tcl_shared_library, tcltk_info.tk_shared_library):
                if p and Path(p).is_file():
                    add_binary(p)

        for _ref, lib_path in bindepend.get_imports(tk_so):
            if lib_path and Path(lib_path).is_file():
                add_binary(lib_path)

        if not seeds:
            return []
        full = bindepend.binary_dependency_analysis(seeds)
        out = []
        for dest_name, src_name, typecode in full:
            if typecode != "BINARY":
                continue
            trg = os.path.dirname(dest_name) or "."
            out.append((src_name, trg))
        return out
    except Exception:
        return []


def _linux_ldd_tcl_tk_closure():
    """Явный ldd по _tkinter + binary_dependency_analysis — добирает libtcl9.0/libtcl9tk, которые граф PyInstaller мог пропустить."""
    if not sys.platform.startswith("linux"):
        return []
    try:
        import _tkinter
    except Exception:
        return []
    tk_so = getattr(_tkinter, "__file__", None)
    if not tk_so:
        return []
    tk_so = os.path.realpath(tk_so)
    if not Path(tk_so).is_file():
        return []
    proc = subprocess.run(
        ["ldd", tk_so],
        capture_output=True,
        text=True,
        timeout=120,
    )
    seeds = []
    pat = re.compile(r"^\s*\S+\s+=>\s+(\S+)\s+\(0x")
    for line in proc.stdout.splitlines():
        m = pat.match(line)
        if not m:
            continue
        resolved = m.group(1)
        if not resolved.startswith("/") or not Path(resolved).is_file():
            continue
        base_l = os.path.basename(resolved).lower()
        if not any(k in base_l for k in ("tcl", "tk", "blt")):
            continue
        seeds.append((os.path.basename(resolved), resolved, "BINARY"))
    if not seeds:
        return []
    return bindepend.binary_dependency_analysis(seeds)


block_cipher = None

datas = [
    (str(ROOT / "data" / "f0_WaasKirf.dat"), "data"),
    (str(ROOT / "config"), "config"),
]

hiddenimports = [
    "src",
    "src.__main__",
    "src.cli",
    "src.gui",
    "src.gui.app",
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
    "matplotlib.backends.backend_tkagg",
    "matplotlib.backends.backend_agg",
    "mpl_toolkits.mplot3d",
    "PIL",
    "PIL._tkinter_finder",
    "kiwisolver",
    "contourpy",
    "dateutil",
    "pyparsing",
    "cycler",
    "fontTools",
    "fontTools.misc",
]

a = Analysis(
    [str(ROOT / "src" / "__main__.py")],
    pathex=[str(ROOT)],
    binaries=_linux_tcl_tk_binaries(),
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[str(ROOT / "packaging" / "pyi_rth_linux_tk_libs.py")],
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
        "pytest",
        "IPython",
        "jupyter",
        "transformers",
        "nvidia",
        "triton",
        "scipy",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

if sys.platform.startswith("linux"):
    try:
        _tcl_tk_extra = _linux_ldd_tcl_tk_closure()
        if _tcl_tk_extra:
            a.binaries = normalize_toc(a.binaries + _tcl_tk_extra)
    except Exception:
        pass

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_exe_kw = dict(
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

if sys.platform.startswith("linux"):
    exe = EXE(
        pyz,
        a.scripts,
        [],
        exclude_binaries=True,
        name="xray-msu-gui",
        **_exe_kw,
    )
    coll = COLLECT(
        exe,
        a.binaries,
        a.zipfiles,
        a.datas,
        strip=False,
        upx=False,
        upx_exclude=[],
        name="xray-msu-gui",
    )
else:
    exe = EXE(
        pyz,
        a.scripts,
        a.binaries,
        a.zipfiles,
        a.datas,
        [],
        name="xray-msu-gui",
        **_exe_kw,
    )
