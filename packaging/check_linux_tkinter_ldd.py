#!/usr/bin/env python3
"""
Проверка перед PyInstaller GUI: _tkinter должен находить libtcl*/libtk* (ldd без «not found»).
Иначе frozen-сборка получит скрипты Tcl в _internal, но без .so — ImportError при запуске.
"""

from __future__ import annotations

import re
import subprocess
import sys


def main() -> int:
    """Проверяет, что ``_tkinter`` разрешает libtcl/libtk через ``ldd``.

    Returns:
        0 при успехе, 1 если import или ldd не прошли или библиотеки не найдены.
    """
    try:
        import _tkinter
    except ImportError as e:
        print(
            "check_linux_tkinter_ldd: не удалось import _tkinter:", e, file=sys.stderr
        )
        return 1

    so = getattr(_tkinter, "__file__", None)
    if not so:
        print("check_linux_tkinter_ldd: у _tkinter нет __file__", file=sys.stderr)
        return 1

    proc = subprocess.run(["ldd", so], capture_output=True, text=True, timeout=120)
    if proc.returncode != 0:
        print(
            "check_linux_tkinter_ldd: ldd завершился с кодом",
            proc.returncode,
            file=sys.stderr,
        )
        if proc.stderr:
            print(proc.stderr, file=sys.stderr)
        return 1

    bad: list[str] = []
    for line in proc.stdout.splitlines():
        if "not found" not in line:
            continue
        if re.search(r"lib(tcl|tk)", line, re.I):
            bad.append(line.strip())

    if not bad:
        return 0

    print(
        "Сборка GUI прервана: для текущего Python модуля _tkinter не разрешаются разделяемые библиотеки Tcl/Tk:",
        file=sys.stderr,
    )
    for x in bad:
        print(" ", x, file=sys.stderr)
    print(file=sys.stderr)
    needs_tcl9 = any("libtcl9" in x for x in bad)

    print(
        "PyInstaller не может упаковать отсутствующие .so.",
        file=sys.stderr,
    )
    if needs_tcl9:
        print(file=sys.stderr)
        print(
            "Обнаружен Tcl 9 (libtcl9*), а в apt часто нет таких пакетов (Ubuntu 22.04 / Debian stable и т.п.).",
            "Автономный CPython из uv при этом ожидает libtcl9.0.so на диске.",
            file=sys.stderr,
        )
        print(
            "Рабочий обход: дистрибутивный Python + python3-tk (libtcl8.6), без автономной сборки uv:",
            file=sys.stderr,
        )
        print(
            "  1) sudo apt install python3-tk   # для вашей версии python3, см. ниже",
            file=sys.stderr,
        )
        print(
            "  2) rm -rf .venv && uv sync --python $(command -v python3) --extra dev",
            file=sys.stderr,
        )
        print(
            "     (или явно: uv sync --python /usr/bin/python3.12 --extra dev — см. requires-python в pyproject.toml)",
            file=sys.stderr,
        )
        print(
            '  3) в pyproject.toml задано [tool.uv] python-preference = "system" — после смены Python пересоздайте .venv.',
            file=sys.stderr,
        )
        print(
            "Если требуется именно Python ≥3.12, а в системе 3.10: поставьте python3.12 из репозитория/PPA и",
            "пакет вида python3.12-tk, затем uv sync --python /usr/bin/python3.12.",
            file=sys.stderr,
        )
        print(file=sys.stderr)

    print(
        "Либо установите рантайм Tcl 9, если он есть в ваших репозиториях (новее Ubuntu / Fedora):",
        file=sys.stderr,
    )
    print("  Debian/Ubuntu: apt search libtcl9", file=sys.stderr)
    print("  Fedora/RHEL:    sudo dnf install tcl tk", file=sys.stderr)
    print(
        "  Проверка:       ldd <путь_к__tkinter__> | grep -E 'tcl|tk'  (без «not found»)",
        file=sys.stderr,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
