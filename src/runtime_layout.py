"""Пути к ресурсам и рабочему каталогу: обычный запуск и PyInstaller (sys._MEIPASS)."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Iterable, Optional

ASF_DAT_FILENAME = "f0_WaasKirf.dat"
# Реальный файл ~100+ KiB; пустой/обрезанный рядом с .exe не должен подменять бандл.
ASF_MIN_BYTES = 4096


def bundle_root() -> Optional[str]:
    """Возвращает корень бандла PyInstaller или None в режиме разработки.

    Returns:
        Путь к ``sys._MEIPASS`` для frozen-приложения; иначе ``None``.
    """
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return sys._MEIPASS
    return None


def application_directory() -> Path:
    """Возвращает каталог приложения.

    Returns:
        Каталог рядом с исполняемым файлом (frozen) или текущий рабочий каталог (dev).
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path.cwd()


def repository_root() -> Path:
    """Возвращает корень репозитория.

    Returns:
        Каталог, содержащий ``data/`` и ``config/``.
    """
    return Path(__file__).resolve().parent.parent


def resource_path(*parts: str) -> Optional[str]:
    """Ищет файл или каталог среди ресурсов приложения.

    Сначала проверяет бандл PyInstaller, затем каталог рядом с бинарником.

    Args:
        *parts: Компоненты относительного пути (например, ``"config"``, ``"foo.yaml"``).

    Returns:
        Абсолютный путь к существующему ресурсу или ``None``, если не найден.
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
    """Перечисляет кандидатов на путь к таблице атомных факторов f₀.

    Yields:
        Уникальные пути к ``data/f0_WaasKirf.dat`` в порядке приоритета.
    """
    rel = Path("data") / ASF_DAT_FILENAME
    seen: set[Path] = set()

    def add(p: Path) -> Optional[Path]:
        """Добавляет путь в множество уже просмотренных.

        Args:
            p: Кандидат на путь к файлу.

        Returns:
            Разрешённый путь, если он ещё не встречался; иначе ``None``.
        """
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
    """Возвращает абсолютный путь к таблице атомных факторов Waas–Kirfel.

    В frozen-сборке приоритет у ``_MEIPASS``, а не у пустого ``data/`` рядом с exe.

    Returns:
        Путь к файлу ``data/f0_WaasKirf.dat`` размером не менее ``ASF_MIN_BYTES`` байт.

    Raises:
        FileNotFoundError: Если подходящий файл не найден ни по одному из кандидатов.
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
    """Устанавливает рабочий каталог рядом с исполняемым файлом (frozen).

    В режиме разработки ничего не делает.
    """
    if getattr(sys, "frozen", False):
        try:
            os.chdir(application_directory())
        except OSError:
            pass


def bundled_config_dir() -> Optional[Path]:
    """Возвращает каталог шаблонов конфигурации внутри бандла.

    Returns:
        Путь к ``config/`` в ``_MEIPASS`` или ``None``, если бандл или каталог отсутствуют.
    """
    br = bundle_root()
    if not br:
        return None
    p = Path(br) / "config"
    return p if p.is_dir() else None


def _seed_file_if_missing(src: Path, dst: Path) -> None:
    """Копирует файл из бандла, если целевой файл ещё не существует.

    Args:
        src: Исходный файл в бандле.
        dst: Целевой путь рядом с исполняемым файлом.
    """
    if dst.exists():
        return
    if src.is_file():
        shutil.copy2(src, dst)


def _ensure_extra_paths_lists_runs(config_dir: Path) -> None:
    """Гарантирует наличие ``runs`` в ``extra_paths.txt``.

    Args:
        config_dir: Каталог пользовательской конфигурации.
    """
    path = config_dir / "extra_paths.txt"
    if not path.is_file():
        path.write_text(
            "# Дополнительные папки со структурами (по одной на строку).\nruns\n",
            encoding="utf-8",
        )
        return
    text = path.read_text(encoding="utf-8")
    has_runs = any(
        ln.strip() == "runs"
        for ln in text.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    )
    if not has_runs:
        with path.open("a", encoding="utf-8") as fh:
            if text and not text.endswith("\n"):
                fh.write("\n")
            fh.write("runs\n")


def ensure_runtime_layout() -> Path:
    """Подготавливает каталоги ``runs/`` и ``config/`` для frozen-приложения.

    В режиме разработки возвращает ``config/`` репозитория без копирования шаблонов.

    Returns:
        Путь к каталогу конфигурации, используемому приложением.
    """
    if not getattr(sys, "frozen", False):
        cfg = repository_root() / "config"
        (repository_root() / "runs").mkdir(parents=True, exist_ok=True)
        return cfg

    ensure_workdir()
    app = application_directory()
    runs_dir = app / "runs"
    config_dir = app / "config"
    runs_dir.mkdir(parents=True, exist_ok=True)
    config_dir.mkdir(parents=True, exist_ok=True)

    src_cfg = bundled_config_dir()
    if src_cfg:
        for item in sorted(src_cfg.iterdir()):
            if item.is_file():
                _seed_file_if_missing(item, config_dir / item.name)

    for name in ("ignore_list.txt", "list_entries.txt"):
        dst = config_dir / name
        if not dst.is_file():
            dst.write_text(
                "# Управляется GUI; строки с # — комментарии.\n",
                encoding="utf-8",
            )

    _ensure_extra_paths_lists_runs(config_dir)
    return config_dir
