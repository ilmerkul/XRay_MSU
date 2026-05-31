"""Графический интерфейс XRay MSU."""

import tkinter as tk

from .app import PowderPatternGUI


def run_gui(*, local: bool = True) -> None:
    """Запускает главное окно приложения.

    Args:
        local: ``True`` — f из Waas–Kirfel; ``False`` — xraylib (``uv sync --extra xraylib``).
    """
    root = tk.Tk()
    root._gui_app = PowderPatternGUI(root, local=local)
    root.mainloop()


__all__ = ["PowderPatternGUI", "run_gui"]
