#!/usr/bin/env python3
"""
Точка входа CLI для PyInstaller (cmd/main.py). Из репозитория: python cmd/main.py.
"""
from __future__ import annotations

import os
import runpy
import sys
from pathlib import Path


def main() -> None:
    if getattr(sys, "frozen", False):
        sys.path.insert(0, sys._MEIPASS)
        os.chdir(Path(sys.executable).parent)
        runpy.run_path(str(Path(sys._MEIPASS) / "cmd" / "main.py"), run_name="__main__")
    else:
        root = Path(__file__).resolve().parent
        runpy.run_path(str(root / "cmd" / "main.py"), run_name="__main__")


if __name__ == "__main__":
    main()
