"""Главное окно приложения XRay MSU."""

import locale

try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except (locale.Error, OSError):
    pass

import tkinter as tk
from tkinter import messagebox

import matplotlib

from ..model.atom.atom import AtomicScatteringFactor
from ..model.pattern.utils import (
    CAGLIOTI_U_DEFAULT,
    CAGLIOTI_V_DEFAULT,
    CAGLIOTI_W_DEFAULT,
)
from ..runtime_layout import asf_data_path

matplotlib.use("TkAgg")

from .atoms import AtomsMixin
from .calculation import CalculationMixin
from .config import ConfigMixin
from .constants import GuiConstants
from .i18n import I18nMixin
from .lattice_ui import LatticeUIMixin
from .menu_bar import MenuBarMixin
from .plot_interaction import PlotInteractionMixin
from .plot_view import PlotViewMixin
from .results import ResultsMixin
from .shortcuts import ShortcutsMixin
from .theme import build_ui_fonts, configure_matplotlib_defaults
from .theme_mixin import ThemeMixin
from .undo import UndoMixin
from .widgets import WidgetsMixin


class PowderPatternGUI(
    GuiConstants,
    I18nMixin,
    ThemeMixin,
    MenuBarMixin,
    ShortcutsMixin,
    UndoMixin,
    WidgetsMixin,
    PlotInteractionMixin,
    ConfigMixin,
    LatticeUIMixin,
    AtomsMixin,
    PlotViewMixin,
    ResultsMixin,
    CalculationMixin,
):
    """Графический интерфейс расчёта порошковой дифрактограммы."""

    def __init__(self, root, *, local: bool = True):
        """Инициализирует окно приложения, переменные состояния и виджеты.

        Args:
            root: Корневое окно ``tk.Tk``.
            local: ``True`` — f из Waas–Kirfel; ``False`` — xraylib.

        Raises:
            SystemExit: Если не удалось загрузить таблицу атомных f₀.
        """
        self.structure_factor_local = local
        configure_matplotlib_defaults()
        self.root = root
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        h = max(600, sh - 100)
        self.root.geometry(f"{sw}x{h}+0+0")
        self.root.minsize(min(900, sw), 500)

        self.name_var = tk.StringVar(value="NaCl")

        self.a_var = tk.DoubleVar(value=5.64)
        self.b_var = tk.DoubleVar(value=5.64)
        self.c_var = tk.DoubleVar(value=5.64)
        self.alpha_var = tk.DoubleVar(value=90.0)
        self.beta_var = tk.DoubleVar(value=90.0)
        self.gamma_var = tk.DoubleVar(value=90.0)
        self.space_group_var = tk.StringVar(value="null")
        # P/I/F/C/A/B — развёртка по центровке (дроби ячейки) при Hall пусто
        self.bravais_centering_var = tk.StringVar(value="P")
        self.language_var = tk.StringVar(value="en")
        self.theme_var = tk.StringVar(value=self._theme_label("dark"))
        self.root.title(self.tr("window_title"))
        self.lattice_family_var = tk.StringVar(value=self._lattice_label("manual"))
        self._lattice_trace_ids = []
        self._lattice_sync_guard = False
        self._cell_entries = {}

        self.atoms = [
            {"element": "Na", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.6},
            {"element": "Na", "x": 0.0, "y": 0.5, "z": 0.5, "occ": 1.0, "biso": 1.6},
            {"element": "Na", "x": 0.5, "y": 0.0, "z": 0.5, "occ": 1.0, "biso": 1.6},
            {"element": "Na", "x": 0.5, "y": 0.5, "z": 0.0, "occ": 1.0, "biso": 1.6},
            {"element": "Cl", "x": 0.5, "y": 0.5, "z": 0.5, "occ": 1.0, "biso": 1.35},
            {"element": "Cl", "x": 0.5, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.35},
            {"element": "Cl", "x": 0.0, "y": 0.5, "z": 0.0, "occ": 1.0, "biso": 1.35},
            {"element": "Cl", "x": 0.0, "y": 0.0, "z": 0.5, "occ": 1.0, "biso": 1.35},
        ]

        self.wavelength_var = tk.DoubleVar(value=1.5418)
        self.wavelength2_enabled_var = tk.BooleanVar(value=False)
        self.wavelength2_var = tk.StringVar(value="")
        self.wl2_intensity_ratio_var = tk.DoubleVar(value=1.0)
        self.tth_start_var = tk.DoubleVar(value=5.0)
        self.tth_end_var = tk.DoubleVar(value=150.0)
        self.tth_step_var = tk.DoubleVar(value=0.02)

        self.U_var = tk.DoubleVar(value=CAGLIOTI_U_DEFAULT)
        self.V_var = tk.DoubleVar(value=CAGLIOTI_V_DEFAULT)
        self.W_var = tk.DoubleVar(value=CAGLIOTI_W_DEFAULT)
        self.scale_var = tk.DoubleVar(value=1.0)
        self.profile_var = tk.StringVar(value=self._profile_label("bar"))
        self.eta_var = tk.DoubleVar(value=0.5)
        self.intensity_units_var = tk.StringVar(value="arbitrary")
        self.normalize_intensity_var = tk.BooleanVar(value=True)
        self.intensity_max_value_var = tk.DoubleVar(value=100.0)
        self.thetam_deg_var = tk.DoubleVar(value=0.0)
        self.multiplicity_metric_rtol_var = tk.DoubleVar(value=1e-7)
        self.multiplicity_metric_atol_var = tk.DoubleVar(value=1e-12)

        self.config_dir = self.find_config_dir()
        try:
            self.asf = AtomicScatteringFactor(asf_data_path())
        except (FileNotFoundError, ValueError, OSError) as exc:
            messagebox.showerror(
                "XRay MSU",
                f"Не удалось загрузить таблицу f₀ (Waas–Kirfel):\n{exc}",
            )
            raise SystemExit(1) from exc
        self.config_files = {}
        self.atoms_frame = None
        self.show_biso_var = tk.BooleanVar(value=False)
        self.label_angles_var = tk.BooleanVar(value=False)
        self.label_angles_hkl_var = tk.BooleanVar(value=False)
        self._atom_header_labels = []
        self._section_content = {}
        self._section_buttons = {}
        self._hkl_hover_cid = None
        self._hkl_hover_peaks = None
        self._hkl_hover_annot = None
        self._plot_peak_data = None
        self._peak_label_artists = []
        self._zoom_selector = None
        self._zoom_reset_cid = None
        self._full_xlim = None
        self._full_ylim = None
        self._wl2_fields_frame = None
        self._eta_entry = None
        self._eta_label = None
        self._caglioti_label = None
        self._caglioti_frame = None
        self._caglioti_entries = []
        self._pattern_entry_widgets = []
        self._profile_combo = None
        self._plot_outer = None
        self.plot_line_width_var = tk.DoubleVar(value=1.6)
        self.plot_antialiased_var = tk.BooleanVar(value=True)
        self.plot_grid_major_var = tk.BooleanVar(value=True)
        self.plot_grid_minor_var = tk.BooleanVar(value=True)
        self.plot_grid_major_alpha_var = tk.DoubleVar(value=0.55)
        self.plot_grid_minor_alpha_var = tk.DoubleVar(value=0.3)
        self.plot_grid_major_lw_var = tk.DoubleVar(value=0.55)
        self.plot_grid_minor_lw_var = tk.DoubleVar(value=0.35)
        self.plot_vlines_var = tk.BooleanVar(value=True)
        self.plot_vline_width_var = tk.DoubleVar(value=0.4)
        self.plot_vline_alpha_var = tk.DoubleVar(value=0.45)
        self.plot_title_show_var = tk.BooleanVar(value=True)
        self.plot_legend_show_var = tk.BooleanVar(value=True)
        self.plot_legend_loc_var = tk.StringVar(value="upper right")
        self.plot_tick_label_size_var = tk.IntVar(value=10)
        self.plot_axis_label_size_var = tk.IntVar(value=0)
        self.plot_title_size_var = tk.IntVar(value=0)
        self.plot_peak_label_size_var = tk.IntVar(value=0)
        self.plot_y_top_margin_var = tk.DoubleVar(value=1.08)
        self.plot_layout_pad_var = tk.DoubleVar(value=1.2)
        self.plot_dpi_var = tk.IntVar(value=100)
        self.plot_aspect_var = tk.DoubleVar(value=1.25)
        self._plot_aspect = 1.25
        self._plot_settings_win = None
        self._shortcuts_win = None
        self._help_guide_win = None
        self._menubar = None
        self._init_undo()
        self._calc_results = []
        self._selected_calc_indices: list[int] = []
        self._calc_listbox = None
        self._calc_tooltip_win = None
        self._calc_tooltip_idx = None
        self._save_option_vars = {}
        self._save_option_state_cache = {}
        self._plot_graph_frame = None
        self._calc_running = False
        self._reflection_cache: dict = {}
        self.input_width = 14
        fonts = build_ui_fonts(self.root)
        self.fonts = fonts
        self.input_font = fonts.ui
        self.label_font = fonts.ui

        self.create_widgets()
        self._apply_gui_theme(redraw_plot=False)
        self._commit_form_state()
        self.scan_config_files()
