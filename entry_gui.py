#!/usr/bin/env python3
"""
Точка входа GUI для PyInstaller. Из репозитория: python entry_gui.py или python -m src.
"""

from __future__ import annotations

import locale
import os
import runpy
import sys
from pathlib import Path

try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except (locale.Error, OSError):
    pass


def main() -> None:
    if getattr(sys, "frozen", False):
        sys.path.insert(0, sys._MEIPASS)
        from src.runtime_layout import ensure_runtime_layout

        ensure_runtime_layout()
    else:
        root = Path(__file__).resolve().parent
        sys.path.insert(0, str(root))
        os.chdir(root)
    runpy.run_module("src", run_name="__main__")


if __name__ == "__main__":
    main()
