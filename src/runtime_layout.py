"""Пути к ресурсам и рабочему каталогу: обычный запуск и PyInstaller (sys._MEIPASS)."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Iterable, Optional

ASF_DAT_FILENAME = "f0_WaasKirf.dat"
# Реальный файл ~100+ KiB; пустой/обрезанный рядом с .exe не должен подменять бандл.
ASF_MIN_BYTES = 4096


def bundle_root() -> Optional[str]:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return None


def application_directory() -> Path:
    """Каталог рядом с .exe / бинарником (frozen) или текущий cwd (dev)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def repository_root() -> Path:
    """Корень репозитория (каталог с data/, config/)."""
    return Path(__file__).resolve().parent.parent


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


def _asf_candidate_paths() -> Iterable[Path]:
    rel = Path("data") / ASF_DAT_FILENAME
    seen: set[Path] = set()

    def add(p: Path) -> Optional[Path]:
        try:
            rp = p.resolve()
        except OSError:
            return None
        if rp in seen:
            return None
        seen.add(rp)
        return rp

    br = bundle_root()
    if br:
        p = add(Path(br) / rel)
        if p is not None:
            yield p

    p = add(repository_root() / rel)
    if p is not None:
        yield p

    # Рядом с .exe — только если файл похож на полную таблицу (не пустая заглушка).
    p = add(application_directory() / rel)
    if p is not None:
        yield p

    if not getattr(sys, "frozen", False):
        p = add(Path.cwd() / rel)
        if p is not None:
            yield p


def asf_data_path() -> str:
    """
    Абсолютный путь к data/f0_WaasKirf.dat.
    В frozen-сборке приоритет у _MEIPASS (данные PyInstaller), не у пустого data/ рядом с exe.
    """
    tried: list[str] = []
    for path in _asf_candidate_paths():
        tried.append(str(path))
        if not path.is_file():
            continue
        try:
            size = path.stat().st_size
        except OSError:
            continue
        if size < ASF_MIN_BYTES:
            continue
        return str(path)
    hint = (
        "Убедитесь, что при сборке в PyInstaller включён data/f0_WaasKirf.dat "
        "(packaging/xray-msu-gui.spec)."
    )
    if getattr(sys, "frozen", False):
        hint += " Переустановите exe из релиза или положите полный файл в data/ рядом с программой."
    raise FileNotFoundError(
        f"Не найден файл таблицы f₀ ({ASF_DAT_FILENAME}, ≥{ASF_MIN_BYTES} байт).\n"
        f"Проверенные пути:\n  " + "\n  ".join(tried or ["(нет)"]) + f"\n{hint}"
    )


def ensure_workdir() -> None:
    """В frozen-приложении писать runs/, images/ рядом с исполняемым файлом."""
    if getattr(sys, "frozen", False):
        try:
            os.chdir(application_directory())
        except OSError:
            pass
