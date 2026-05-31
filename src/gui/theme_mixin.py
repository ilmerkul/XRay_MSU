"""Переключение светлой и тёмной темы GUI."""

from __future__ import annotations

from tkinter import ttk

from .theme import (
    THEMES,
    UiFonts,
    apply_mpl_theme,
    apply_tk_widget_colors,
    build_ui_fonts,
    configure_ttk_theme,
)


class ThemeMixin:
    """Миксин: палитра, шрифты и стиль matplotlib."""

    THEME_LABELS_BY_LANG = {
        "ru": {"light": "Свет", "dark": "Тём"},
        "en": {"light": "Light", "dark": "Dark"},
    }

    def _theme_label(self, key: str) -> str:
        lang = self.language_var.get().strip().lower()
        return self.THEME_LABELS_BY_LANG.get(lang, self.THEME_LABELS_BY_LANG["en"]).get(
            key, key
        )

    def _theme_key(self) -> str:
        label = self.theme_var.get().strip()
        for key in ("light", "dark"):
            for labels in self.THEME_LABELS_BY_LANG.values():
                if labels.get(key) == label:
                    return key
        return "light"

    def _current_theme(self):
        return THEMES[self._theme_key()]

    def _set_theme_by_key(self, key: str) -> None:
        self.theme_var.set(self._theme_label(key))

    def _apply_gui_theme(self, redraw_plot: bool = True) -> None:
        """Применяет текущую тему к ttk, tk и графику."""
        theme = self._current_theme()
        self.fonts: UiFonts = build_ui_fonts(self.root)
        self.input_font = self.fonts.ui
        self.label_font = self.fonts.ui
        style = ttk.Style(self.root)
        configure_ttk_theme(style, theme, self.fonts)
        apply_tk_widget_colors(
            self.root,
            theme,
            self.fonts,
            main_paned=getattr(self, "_main_paned", None),
            scroll_canvas=getattr(self, "_scroll_canvas", None),
        )
        if hasattr(self, "figure") and hasattr(self, "ax"):
            apply_mpl_theme(self.figure, self.ax, theme, self.fonts)
            if redraw_plot and getattr(self, "_selected_calc_indices", None):
                selected = self._get_selected_calc_results()
                if selected:
                    self._display_calc_results(selected)
            elif hasattr(self, "canvas"):
                self.canvas.draw_idle()

    def _on_theme_selected(self, _event=None) -> None:
        self._apply_gui_theme(redraw_plot=True)
