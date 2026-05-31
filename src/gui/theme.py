"""Светлая и тёмная темы оформления GUI."""

from __future__ import annotations

import os
import tkinter as tk
import tkinter.font as tkfont
from dataclasses import dataclass
from pathlib import Path
from tkinter import ttk

from matplotlib.figure import Figure

_TK_UI_FONT = "XRayMSUUi"
_TK_UI_FONT_BOLD = "XRayMSUUiBold"
_MPL_UI_FAMILY = "DejaVu Sans"


def configure_matplotlib_defaults() -> None:
    """Единые шрифты matplotlib: DejaVu Sans и mathtext с θ, ° и др."""
    import matplotlib as mpl

    mpl.rcParams["font.family"] = _MPL_UI_FAMILY
    mpl.rcParams["mathtext.fontset"] = "dejavusans"


@dataclass(frozen=True)
class GuiTheme:
    name: str
    bg: str
    fg: str
    surface: str
    surface_alt: str
    border: str
    border_soft: str
    accent: str
    accent_hover: str
    accent_fg: str
    accent_soft: str
    entry_bg: str
    muted: str
    plot_bg: str
    plot_fg: str
    grid: str
    grid_minor: str
    mpl_line: str
    tooltip_bg: str
    tooltip_fg: str
    sash: str


@dataclass(frozen=True)
class UiFonts:
    family: str
    mpl_family: str
    ui: tuple[str, int]
    ui_small: tuple[str, int]
    heading: tuple[str, int, str]
    plot_label: tuple[str, int]
    plot_tick: tuple[str, int]
    plot_title: tuple[str, int, str]


THEMES: dict[str, GuiTheme] = {
    "light": GuiTheme(
        name="light",
        bg="#edf1f5",
        fg="#1a2332",
        surface="#edf1f5",
        surface_alt="#ffffff",
        border="#c8d0da",
        border_soft="#dde3ea",
        accent="#0b7285",
        accent_hover="#087f8c",
        accent_fg="#ffffff",
        accent_soft="#e3f6f8",
        entry_bg="#ffffff",
        muted="#5f6b7a",
        plot_bg="#fafbfc",
        plot_fg="#1c2430",
        grid="#d5dbe3",
        grid_minor="#e8ecf1",
        mpl_line="#0b7285",
        tooltip_bg="#ffffff",
        tooltip_fg="#1c2430",
        sash="#b8c2ce",
    ),
    "dark": GuiTheme(
        name="dark",
        bg="#12151a",
        fg="#e8ebef",
        surface="#12151a",
        surface_alt="#1a1f27",
        border="#3a424f",
        border_soft="#2c333d",
        accent="#22b8cf",
        accent_hover="#3bc9db",
        accent_fg="#0b1218",
        accent_soft="#16343b",
        entry_bg="#252b35",
        muted="#9aa3af",
        plot_bg="#161b22",
        plot_fg="#e8ebef",
        grid="#2f3640",
        grid_minor="#232830",
        mpl_line="#3bc9db",
        tooltip_bg="#252b35",
        tooltip_fg="#e8ebef",
        sash="#3a424f",
    ),
}

_UI_FAMILIES = (
    "Noto Sans",
    "Liberation Sans",
    "DejaVu Sans",
    "Free Helvetian",
    "Helvetica",
    "Nimbus Sans L",
    "Inter",
    "IBM Plex Sans",
    "Source Sans 3",
    "Source Sans Pro",
    "Ubuntu",
    "Segoe UI",
    "Tahoma",
)


def _available_families() -> set[str]:
    try:
        return set(tkfont.families())
    except tk.TclError:
        return set()


def _family_lookup(available: set[str]) -> dict[str, str]:
    return {name.lower(): name for name in available}


def _match_family(candidates: tuple[str, ...], available: set[str]) -> str | None:
    """Находит первое совпадение среди установленных семейств (без учёта регистра)."""
    lookup = _family_lookup(available)
    for candidate in candidates:
        key = candidate.lower()
        if key in lookup:
            return lookup[key]
    return None


def _default_tk_family(root: tk.Misc | None) -> str:
    if root is not None:
        try:
            return tkfont.nametofont("TkDefaultFont").actual("family")
        except tk.TclError:
            pass
    return "sans-serif"


def _matplotlib_ttf(filename: str) -> Path | None:
    try:
        import matplotlib as mpl

        path = Path(mpl.get_data_path()) / "fonts" / "ttf" / filename
        return path if path.is_file() else None
    except (ImportError, OSError):
        return None


def _register_tk_font(root: tk.Misc, tk_name: str, ttf_file: str, size: int) -> bool:
    """Регистрирует TTF из matplotlib для Tk, если сборка поддерживает ``-file``."""
    ttf = _matplotlib_ttf(ttf_file)
    if ttf is None:
        return False
    try:
        root.tk.call("font", "create", tk_name, "-file", str(ttf), "-size", size)
        return True
    except tk.TclError:
        return False


def _setup_tk_ui_fonts(root: tk.Misc | None, ui_size: int) -> tuple[str, tuple, tuple]:
    """Возвращает имя шрифта Tk и кортежи (ui, heading) для ttk."""
    available = _available_families()
    if root is not None and _register_tk_font(
        root, _TK_UI_FONT, "DejaVuSans.ttf", ui_size
    ):
        heading: tuple = (_TK_UI_FONT_BOLD, ui_size + 1)
        if _register_tk_font(
            root, _TK_UI_FONT_BOLD, "DejaVuSans-Bold.ttf", ui_size + 1
        ):
            pass
        else:
            heading = (_TK_UI_FONT, ui_size + 1, "bold")
        return _TK_UI_FONT, (_TK_UI_FONT, ui_size), heading

    if os.name == "nt":
        ui_candidates = ("Segoe UI Variable Text", "Segoe UI", "Tahoma") + _UI_FAMILIES
    else:
        ui_candidates = _UI_FAMILIES
    family = _match_family(ui_candidates, available) or _default_tk_family(root)
    ui = (family, ui_size)
    heading = (family, ui_size + 1, "bold")
    return family, ui, heading


def mpl_plot_xlabel(lang: str) -> str:
    """Подпись оси 2θ для matplotlib (mathtext, корректная θ)."""
    unit = "град" if lang.strip().lower().startswith("ru") else "deg"
    return rf"$2\theta$ ({unit})"


def mpl_angle_label(angle: float) -> str:
    """Подпись угла 2θ на графике (mathtext)."""
    return rf"${angle:.2f}^\circ$"


def mpl_hover_peak_text(hkl: str, angle: float) -> str:
    """Текст всплывающей подсказки hkl + угол."""
    return rf"$\mathrm{{{hkl}}}$" + "\n" + rf"$2\theta = {angle:.3f}^\circ$"


def build_ui_fonts(root: tk.Misc | None = None) -> UiFonts:
    """Подбирает семейства и размеры шрифтов под платформу."""
    ui_size = 11
    family, ui, heading = _setup_tk_ui_fonts(root, ui_size)
    return UiFonts(
        family=family,
        mpl_family=_MPL_UI_FAMILY,
        ui=ui,
        ui_small=ui,
        heading=heading,
        plot_label=(family, ui_size),
        plot_tick=(family, ui_size - 1),
        plot_title=heading,
    )


def pick_ui_font(size: int = 12) -> tuple[str, int]:
    """Совместимость: возвращает основной UI-шрифт."""
    fonts = build_ui_fonts()
    return (fonts.family, size)


def configure_ttk_theme(style: ttk.Style, theme: GuiTheme, fonts: UiFonts) -> None:
    """Применяет палитру и именованные стили ttk."""
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure(
        ".",
        background=theme.bg,
        foreground=theme.fg,
        font=fonts.ui,
        bordercolor=theme.border_soft,
    )
    style.configure("TFrame", background=theme.bg)
    style.configure(
        "Card.TFrame",
        background=theme.surface,
    )
    style.configure(
        "Inset.TLabel",
        background=theme.surface_alt,
        foreground=theme.muted,
        font=fonts.ui_small,
    )
    style.configure(
        "InsetHead.TLabel",
        background=theme.surface_alt,
        foreground=theme.fg,
        font=fonts.heading,
    )
    style.configure(
        "TLabel",
        background=theme.bg,
        foreground=theme.fg,
        font=fonts.ui,
    )
    style.configure(
        "Muted.TLabel",
        background=theme.bg,
        foreground=theme.muted,
        font=fonts.ui_small,
    )
    style.configure(
        "Card.TLabelframe",
        background=theme.surface,
        bordercolor=theme.border,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Card.TLabelframe.Label",
        background=theme.surface,
        foreground=theme.fg,
        font=fonts.heading,
    )
    style.configure(
        "Inner.TLabelframe",
        background=theme.surface_alt,
        bordercolor=theme.border_soft,
        borderwidth=1,
        relief="solid",
    )
    style.configure(
        "Inner.TLabelframe.Label",
        background=theme.surface_alt,
        foreground=theme.muted,
        font=fonts.ui_small,
    )
    style.configure(
        "TButton",
        background=theme.surface,
        foreground=theme.fg,
        bordercolor=theme.border,
        focusthickness=1,
        padding=(12, 6),
        font=fonts.ui,
    )
    style.map(
        "TButton",
        background=[
            ("active", theme.surface_alt),
            ("pressed", theme.border_soft),
        ],
        foreground=[("active", theme.fg), ("pressed", theme.fg)],
    )
    style.configure(
        "Primary.TButton",
        background=theme.accent,
        foreground=theme.accent_fg,
        bordercolor=theme.accent,
        padding=(16, 8),
        font=fonts.heading,
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", theme.accent_hover),
            ("pressed", theme.accent_hover),
        ],
        foreground=[("active", theme.accent_fg), ("pressed", theme.accent_fg)],
    )
    style.configure(
        "Secondary.TButton",
        background=theme.surface,
        foreground=theme.fg,
        bordercolor=theme.border,
        padding=(12, 6),
        font=fonts.ui,
    )
    style.map(
        "Secondary.TButton",
        background=[
            ("active", theme.surface_alt),
            ("pressed", theme.border_soft),
        ],
    )
    style.configure(
        "Section.TButton",
        background=theme.surface,
        foreground=theme.fg,
        bordercolor=theme.border_soft,
        anchor="w",
        padding=(12, 8),
        font=fonts.heading,
    )
    style.map(
        "Section.TButton",
        background=[
            ("active", theme.surface_alt),
            ("pressed", theme.accent_soft),
        ],
    )
    style.configure(
        "TEntry",
        fieldbackground=theme.entry_bg,
        foreground=theme.fg,
        insertcolor=theme.accent,
        bordercolor=theme.border,
        padding=4,
        font=fonts.ui,
    )
    style.configure(
        "TCombobox",
        fieldbackground=theme.entry_bg,
        background=theme.surface,
        foreground=theme.fg,
        arrowcolor=theme.muted,
        bordercolor=theme.border,
        padding=4,
        font=fonts.ui,
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", theme.entry_bg)],
        foreground=[("readonly", theme.fg)],
    )
    style.configure(
        "TCheckbutton",
        background=theme.bg,
        foreground=theme.fg,
        font=fonts.ui_small,
    )
    style.map("TCheckbutton", background=[("active", theme.bg)])
    style.configure(
        "Card.TCheckbutton",
        background=theme.surface,
        foreground=theme.fg,
        font=fonts.ui_small,
    )
    style.map("Card.TCheckbutton", background=[("active", theme.surface)])
    style.configure(
        "CardInner.TCheckbutton",
        background=theme.surface_alt,
        foreground=theme.fg,
        font=fonts.ui_small,
    )
    style.map("CardInner.TCheckbutton", background=[("active", theme.surface_alt)])
    style.configure(
        "Inset.TCheckbutton",
        background=theme.surface_alt,
        foreground=theme.fg,
        font=fonts.ui_small,
    )
    style.map("Inset.TCheckbutton", background=[("active", theme.surface_alt)])
    style.configure(
        "TScrollbar",
        background=theme.surface_alt,
        troughcolor=theme.bg,
        bordercolor=theme.bg,
        arrowcolor=theme.muted,
    )
    style.map(
        "TScrollbar",
        background=[("active", theme.border)],
    )
    style.configure("TSeparator", background=theme.border_soft)


def apply_tk_widget_colors(
    root: tk.Misc,
    theme: GuiTheme,
    fonts: UiFonts,
    *,
    main_paned: tk.Panedwindow | None = None,
    scroll_canvas: tk.Canvas | None = None,
) -> None:
    """Обновляет классические tk-виджеты и разделитель панелей."""
    root.configure(bg=theme.bg)
    root.option_add("*Font", fonts.ui)

    list_opt = {
        "bg": theme.entry_bg,
        "fg": theme.fg,
        "selectbackground": theme.accent,
        "selectforeground": theme.accent_fg,
        "font": fonts.ui_small,
        "highlightthickness": 1,
        "highlightbackground": theme.border,
        "highlightcolor": theme.accent,
        "borderwidth": 0,
        "relief": "flat",
        "activestyle": "none",
    }

    if main_paned is not None:
        try:
            main_paned.configure(
                bg=theme.bg,
                sashwidth=5,
                sashrelief=tk.FLAT,
                showhandle=False,
                opaqueresize=True,
            )
        except tk.TclError:
            pass

    if scroll_canvas is not None:
        try:
            scroll_canvas.configure(bg=theme.bg, highlightthickness=0)
        except tk.TclError:
            pass

    def walk(w: tk.Misc) -> None:
        cls = w.winfo_class()
        try:
            if cls in ("Canvas", "Frame", "Panedwindow"):
                w.configure(bg=theme.bg, highlightthickness=0)
            elif cls == "Listbox":
                w.configure(**list_opt)
        except tk.TclError:
            pass
        for child in w.winfo_children():
            walk(child)

    walk(root)


def apply_mpl_theme(
    fig: Figure, ax, theme: GuiTheme, fonts: UiFonts | None = None
) -> None:
    """Стилизует оси matplotlib под текущую тему."""
    fonts = fonts or build_ui_fonts()
    fig.patch.set_facecolor(theme.plot_bg)
    ax.set_facecolor(theme.plot_bg)
    ax.tick_params(
        colors=theme.plot_fg,
        labelcolor=theme.plot_fg,
        labelsize=fonts.plot_tick[1],
        width=0.8,
        length=4,
    )
    ax.xaxis.label.set_color(theme.plot_fg)
    ax.yaxis.label.set_color(theme.plot_fg)
    ax.title.set_color(theme.plot_fg)
    for label in ax.get_xticklabels() + ax.get_yticklabels():
        label.set_fontfamily(fonts.mpl_family)
    ax.xaxis.label.set_fontfamily(fonts.mpl_family)
    ax.yaxis.label.set_fontfamily(fonts.mpl_family)
    ax.title.set_fontfamily(fonts.mpl_family)
    for spine in ax.spines.values():
        spine.set_color(theme.border_soft)
        spine.set_linewidth(0.8)
    ax.grid(
        True,
        axis="both",
        which="major",
        color=theme.grid,
        linewidth=0.7,
        alpha=0.85,
    )
    if ax.xaxis.get_minor_locator() is not None:
        ax.grid(
            True,
            axis="x",
            which="minor",
            color=theme.grid_minor,
            linewidth=0.45,
            alpha=0.65,
        )
    _sync_mpl_text_colors(ax, theme, fonts)
    legend = ax.get_legend()
    if legend is not None:
        frame = legend.get_frame()
        frame.set_facecolor(theme.surface_alt)
        frame.set_edgecolor(theme.border_soft)
        frame.set_alpha(0.94)
        for text in legend.get_texts():
            text.set_color(theme.plot_fg)
            text.set_fontfamily(fonts.mpl_family)


def _sync_mpl_text_colors(ax, theme: GuiTheme, fonts: UiFonts) -> None:
    """Обновляет цвет подписей пиков (не трогает tooltip с bbox)."""
    for text in ax.texts:
        if text.get_bbox_patch() is not None:
            continue
        text.set_color(theme.plot_fg)
        label = text.get_text()
        if "$" not in label:
            text.set_fontfamily(fonts.mpl_family)
