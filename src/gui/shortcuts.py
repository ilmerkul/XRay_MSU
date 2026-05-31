"""Глобальные сочетания клавиш GUI."""

from __future__ import annotations

import tkinter as tk
from collections.abc import Callable
from tkinter import ttk


class ShortcutsMixin:
    """Миксин: регистрация горячих клавиш и справка по ним."""

    def _shortcut_bindings(self) -> tuple[tuple[str, str, Callable], ...]:
        """(последовательность bind, accelerator для меню, обработчик)."""
        return (
            ("<Control-o>", "Ctrl+O", self._open_config_file),
            ("<Control-s>", "Ctrl+S", self._save_selected_result),
            ("<Control-p>", "Ctrl+P", self._print_pattern),
            ("<Control-z>", "Ctrl+Z", self._undo_last_action),
            ("<Control-g>", "Ctrl+G", self._open_plot_settings_dialog),
            ("<Control-r>", "Ctrl+R", self._reset_zoom),
            ("<F5>", "F5", self.generate_pattern),
            ("<Control-Return>", "Ctrl+Enter", self.generate_pattern),
            ("<Control-Delete>", "Ctrl+Delete", self._delete_selected_calc_results),
            ("<F1>", "F1", self._show_help_guide_dialog),
            ("<Control-q>", "Ctrl+Q", lambda _e=None: self.root.quit()),
        )

    def _bind_app_shortcuts(self) -> None:
        """Регистрирует глобальные сочетания клавиш."""
        for seq, _accel, handler in self._shortcut_bindings():
            self.root.bind_all(seq, handler, add="+")

    def _shortcut_help_rows(self) -> list[tuple[str, str]]:
        """Строки справки: (ключ локализации, подпись клавиш)."""
        return [
            ("shortcut_open_config", "Ctrl+O"),
            ("shortcut_save", "Ctrl+S"),
            ("shortcut_print", "Ctrl+P"),
            ("shortcut_calc", "F5 / Ctrl+Enter"),
            ("shortcut_undo", "Ctrl+Z"),
            ("shortcut_plot_settings", "Ctrl+G"),
            ("shortcut_reset_zoom", "Ctrl+R"),
            ("shortcut_delete_result", "Delete / Ctrl+Delete"),
            ("shortcut_quit", "Ctrl+Q"),
            ("shortcut_help", "F1"),
        ]

    def _show_shortcuts_dialog(self) -> None:
        """Диалог со списком сочетаний клавиш."""
        if getattr(self, "_shortcuts_win", None) is not None:
            try:
                if self._shortcuts_win.winfo_exists():
                    self._shortcuts_win.lift()
                    return
            except tk.TclError:
                pass

        theme = self._current_theme()
        win = tk.Toplevel(self.root)
        self._shortcuts_win = win
        win.title(self.tr("menu_help_shortcuts"))
        win.transient(self.root)
        win.resizable(False, False)
        win.configure(bg=theme.bg)

        frame = ttk.Frame(win, padding=(20, 16))
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(
            frame,
            text=self.tr("shortcuts_intro"),
            style="Muted.TLabel",
            wraplength=420,
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        for row, (label_key, accel) in enumerate(self._shortcut_help_rows(), start=1):
            ttk.Label(frame, text=self.tr(label_key)).grid(
                row=row, column=0, sticky="w", padx=(0, 16), pady=2
            )
            ttk.Label(frame, text=accel, style="Muted.TLabel").grid(
                row=row, column=1, sticky="e", pady=2
            )

        ttk.Button(
            frame,
            text=self.tr("plot_settings_close"),
            command=win.destroy,
            style="Secondary.TButton",
        ).grid(
            row=len(self._shortcut_help_rows()) + 1, column=1, sticky="e", pady=(12, 0)
        )

        win.protocol("WM_DELETE_WINDOW", win.destroy)
