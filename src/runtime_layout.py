"""Пути к ресурсам и рабочему каталогу: обычный запуск и PyInstaller (sys._MEIPASS)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional


def bundle_root() -> Optional[str]:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return None


def application_directory() -> Path:
    """Каталог рядом с .exe / бинарником (frozen) или текущий cwd (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def resource_path(*parts: str) -> Optional[str]:
    """
    Файл или каталог: сначала внутри бандла PyInstaller, затем рядом с бинарником,
    иначе None (вызывающий может откатиться на относительный путь от cwd).
    """
    br = bundle_root()
    if br:
        p = Path(br).joinpath(*parts)
        if p.exists():
            return str(p)
    ext = application_directory().joinpath(*parts)
    if ext.exists():
        return str(ext)
    return None


def ensure_workdir() -> None:
    """В frozen-приложении писать runs/, images/ рядом с исполняемым файлом."""
    if getattr(sys, "frozen", False):
        try:
            os.chdir(application_directory())
        except OSError:
            pass
