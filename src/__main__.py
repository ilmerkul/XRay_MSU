"""Точка входа: ``python -m src [--gui|--cli] [--local|--no-local] [config.yaml]``."""

from __future__ import annotations

import argparse
import locale
import os
import sys
from pathlib import Path


def _bootstrap() -> None:
    """Настраивает локаль, ``sys.path`` и рабочий каталог (dev / PyInstaller)."""
    try:
        locale.setlocale(locale.LC_NUMERIC, "C")
    except (locale.Error, OSError):
        pass

    if getattr(sys, "frozen", False):
        sys.path.insert(0, sys._MEIPASS)
        from src.runtime_layout import ensure_runtime_layout

        ensure_runtime_layout()
        return

    root = Path(__file__).resolve().parent.parent
    root_s = str(root)
    if root_s not in sys.path:
        sys.path.insert(0, root_s)
    os.chdir(root)


def _frozen_default_cli() -> bool:
    """Определяет режим CLI по имени frozen-бинарника (``xray-msu-cli``)."""
    if not getattr(sys, "frozen", False):
        return False
    stem = Path(sys.executable).stem.lower()
    return "cli" in stem and "gui" not in stem


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m src",
        description="XRay MSU: расчёт порошковой дифрактограммы (GUI или CLI).",
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--cli",
        action="store_true",
        help="режим CLI: расчёт по YAML-конфигу",
    )
    mode.add_argument(
        "--gui",
        action="store_true",
        help="режим GUI (по умолчанию)",
    )
    parser.add_argument(
        "--local",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="атомные f из Waas–Kirfel (True, по умолчанию) или xraylib (False)",
    )
    parser.add_argument(
        "config",
        nargs="?",
        default=None,
        help="путь к YAML (без аргумента — интерактивный выбор через questionary)",
    )
    return parser


def main(argv: list[str] | None = None) -> None:
    """Запускает GUI или CLI в зависимости от флагов и имени исполняемого файла."""
    _bootstrap()
    args = _build_parser().parse_args(argv)

    use_cli = args.cli or (not args.gui and _frozen_default_cli())
    if use_cli:
        from src.cli import run_cli

        run_cli(args.config, local=args.local)
        return

    from src.gui import run_gui

    run_gui(local=args.local)


if __name__ == "__main__":
    main()
