"""Графический интерфейс XRay MSU."""


def run_gui(*, local: bool = True) -> None:
    """Запускает главное окно приложения.

    Args:
        local: ``True`` — f из Waas–Kirfel; ``False`` — xraylib (``uv sync --extra xraylib``).
    """
    import tkinter as tk

    from .app import PowderPatternGUI

    root = tk.Tk()
    root._gui_app = PowderPatternGUI(root, local=local)
    root.mainloop()


def __getattr__(name: str):
    if name == "PowderPatternGUI":
        from .app import PowderPatternGUI

        return PowderPatternGUI
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["PowderPatternGUI", "run_gui"]
