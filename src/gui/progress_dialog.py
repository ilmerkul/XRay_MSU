"""Модальное окно прогресса длительного расчёта."""

from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from .theme import GuiTheme, UiFonts, configure_ttk_theme


class ProgressDialog:
    """Неблокирующее по UI окно с полосой прогресса (0–100 %)."""

    def __init__(
        self,
        parent: tk.Misc,
        title: str,
        message: str,
        theme: GuiTheme,
        fonts: UiFonts,
    ) -> None:
        self._parent = parent
        self.win = tk.Toplevel(parent)
        self.win.title(title)
        self.win.transient(parent)
        self.win.resizable(False, False)
        self.win.protocol("WM_DELETE_WINDOW", lambda: None)
        self.win.configure(bg=theme.bg)

        style = ttk.Style(self.win)
        configure_ttk_theme(style, theme, fonts)

        frame = ttk.Frame(self.win, padding=(24, 20))
        frame.pack(fill=tk.BOTH, expand=True)

        self._status_var = tk.StringVar(value=message)
        ttk.Label(frame, textvariable=self._status_var, wraplength=320).pack(
            anchor="w", pady=(0, 12)
        )
        self._bar = ttk.Progressbar(frame, mode="determinate", maximum=100, length=320)
        self._bar.pack(fill=tk.X)
        self._pct_var = tk.StringVar(value="0 %")
        ttk.Label(frame, textvariable=self._pct_var, style="Muted.TLabel").pack(
            anchor="e", pady=(8, 0)
        )

        self.win.update_idletasks()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        w = self.win.winfo_width()
        h = self.win.winfo_height()
        self.win.geometry(f"+{px + max((pw - w) // 2, 0)}+{py + max((ph - h) // 2, 0)}")
        self.win.grab_set()
        parent.update_idletasks()

    def set_progress(self, fraction: float, message: str | None = None) -> None:
        """Обновляет полосу (``fraction`` от 0 до 1) и опционально подпись."""
        pct = max(0.0, min(1.0, float(fraction))) * 100.0
        self._bar["value"] = pct
        self._pct_var.set(f"{pct:.0f} %")
        if message is not None:
            self._status_var.set(message)
        self.win.update_idletasks()

    def close(self) -> None:
        """Закрывает окно и снимает захват ввода."""
        try:
            self.win.grab_release()
        except tk.TclError:
            pass
        try:
            self.win.destroy()
        except tk.TclError:
            pass
