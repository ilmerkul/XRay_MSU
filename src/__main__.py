import fnmatch
import glob
import json
import locale
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# До import tkinter: на Windows с LC_NUMERIC≠C виджеты DoubleVar/ввод часто ломаются (запятая vs точка).
try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except (locale.Error, OSError):
    pass

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import matplotlib
import numpy as np
import yaml
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator
from matplotlib.widgets import RectangleSelector

from .model.atom.atom import Atom, AtomicScatteringFactor
from .model.crystal.crystal import Crystal
from .model.crystal.utils import expand_atoms_bravais_centering
from .model.pattern.plot import Plot
from .model.pattern.powder import PowderPattern
from .model.pattern.utils import (
    CAGLIOTI_U_DEFAULT,
    CAGLIOTI_V_DEFAULT,
    CAGLIOTI_W_DEFAULT,
    normalize_profile,
)
from .runtime_layout import (
    application_directory,
    asf_data_path,
    ensure_runtime_layout,
    resource_path,
)

matplotlib.use("TkAgg")


def _parse_float_locale(s: str) -> float:
    """Парсинг числа из полей ввода: запятая как десятичный разделитель (локали Windows)."""
    t = str(s).strip().replace(",", ".").replace(" ", "")
    return float(t)


def _safe_double_get(var, field_label: str):
    """DoubleVar.get() при неверном формате даёт TclError (часто на Windows)."""
    try:
        return var.get()
    except tk.TclError:
        messagebox.showerror(
            "Input Error",
            f"Invalid number in {field_label}. Use a dot as decimal separator (e.g. 1.5).",
        )
        return None


class PowderPatternGUI:
    SAVE_OUTPUT_KEYS = (
        "txt",
        "json",
        "powder_png",
        "cell_png",
        "G_csv",
        "Gstar_csv",
    )
    LATTICE_FAMILY_KEYS = (
        "manual",
        "cubic",
        "tetragonal",
        "orthorhombic",
        "hexagonal",
        "rhombohedral",
        "monoclinic",
    )
    LATTICE_FAMILY_LABELS_BY_LANG = {
        "ru": {
            "manual": "Нет (вручную)",
            "cubic": "Кубическая (a=b=c, 90°)",
            "tetragonal": "Тетрагональная (a=b, 90°)",
            "orthorhombic": "Орторомбическая (90°)",
            "hexagonal": "Гексагональная (a=b, γ=120°)",
            "rhombohedral": "Ромбоэдр. (a=b=c, α=β=γ)",
            "monoclinic": "Моноклинная (α=γ=90°)",
        },
        "en": {
            "manual": "Manual (no constraints)",
            "cubic": "Cubic (a=b=c, 90°)",
            "tetragonal": "Tetragonal (a=b, 90°)",
            "orthorhombic": "Orthorhombic (90°)",
            "hexagonal": "Hexagonal (a=b, γ=120°)",
            "rhombohedral": "Rhombohedral (a=b=c, α=β=γ)",
            "monoclinic": "Monoclinic (α=γ=90°)",
        },
    }
    LANGUAGE_LABELS = {"ru": "Русский", "en": "English"}
    PROFILE_KEYS = ("bar", "gaussian", "lorentzian", "pseudo-voigt")
    PROFILE_LABELS_BY_LANG = {
        "ru": {
            "bar": "штрих",
            "gaussian": "gaussian",
            "lorentzian": "lorentzian",
            "pseudo-voigt": "pseudo-voigt",
        },
        "en": {
            "bar": "bar",
            "gaussian": "gaussian",
            "lorentzian": "lorentzian",
            "pseudo-voigt": "pseudo-voigt",
        },
    }
    UI_TEXTS = {
        "ru": {
            "config_frame": "Загрузка данных из списка",
            "select_config": "Список:",
            "refresh_list": "Обновить список",
            "add_config_file": "Добавить файл…",
            "remove_config": "Удалить из списка",
            "add_config_file_title": "Выберите файл конфигурации",
            "remove_config_confirm": "Удалить «{name}» из списка?",
            "config_removed": "«{name}» удалён из списка.",
            "config_added": "Добавлено: {path}",
            "config_add_failed": "Не удалось добавить:\n{error}",
            "config_remove_failed": "Не удалось убрать:\n{error}",
            "config_nothing_selected": "Выберите пункт в списке.",
            "config_invalid_path": "Файл или папка не найдены:\n{path}",
            "language": "Язык:",
            "crystal_params": "Параметры кристалла",
            "centering": "Тип ячейки:",
            "system": "Сингония:",
            "name": "Имя файла:",
            "element_col": "Элемент",
            "a_axis": "a (Å):",
            "b_axis": "b (Å):",
            "c_axis": "c (Å):",
            "alpha_angle": "α (°):",
            "beta_angle": "β (°):",
            "gamma_angle": "γ (°):",
            "atoms": "Атомы",
            "show_biso": "Показать колонку B_iso",
            "add_atom": "Добавить атом",
            "remove_atom": "Удалить последний атом",
            "pattern_params": "Параметры дифракции",
            "wavelength1": "Длина волны (Å):",
            "wavelength2": "Длина волны 2 (Å):",
            "wl2_ratio": "I(λ2)/I(λ1):",
            "tth_range": "2θ диапазон:",
            "step": "шаг",
            "profile": "Профиль:",
            "pseudo_voigt_eta": "η (pseudo-Voigt):",
            "caglioti": "Кальотти U, V, W:",
            "thetam": "θm (град, поляризация):",
            "use_wl2": "Использовать вторую длину волны",
            "generate_pattern": "Рассчитать дифрактограмму",
            "reset_zoom": "Вернуть исх. масштаб",
            "plot_area": "Дифрактограмма",
            "calc_results": "Рассчитанные дифрактограммы",
            "save_to_folder": "Сохранить в папку…",
            "save_pick_folder": "Выберите папку для сохранения",
            "save_files_group": "Файлы для сохранения:",
            "save_file_txt": "Таблица отражений (.txt)",
            "save_file_json": "Отражения JSON (.json)",
            "save_file_powder_png": "Дифрактограмма (.png)",
            "save_file_cell_png": "Схема ячейки (.png)",
            "save_file_G_csv": "Матрица G (.csv)",
            "save_file_Gstar_csv": "Матрица G* (.csv)",
            "save_nothing_selected": "Отметьте хотя бы один тип файла.",
            "save_no_result_selected": "Выберите дифрактограмму в списке.",
            "save_success": "Сохранено в:\n{path}",
            "save_failed": "Не удалось сохранить:\n{error}",
            "calc_done_message": (
                "Расчёт добавлен в список справа.\n"
                "Файлы сохранены в runs/{name}/\n"
                "Длины волн: {wl_msg}{ratio_msg}"
            ),
            "label_reflection_angles": "Подписи углов 2θ",
            "label_reflection_angles_hkl": "Показать углы и hkl",
            "hover_angle": "2θ = {angle:.3f}°",
            "print_pattern": "Печать",
            "warning_title": "Предупреждение",
            "error_title": "Ошибка",
            "input_error_title": "Ошибка ввода",
            "no_pattern_to_print": "Сначала постройте дифрактограмму.",
            "printer_not_found": "Не найден доступный механизм печати в системе.",
            "print_failed": "Не удалось отправить на печать:\n{error}",
            "print_sent": "График отправлен на печать.",
            "at_least_one_atom": "Нужен хотя бы один атом.",
            "failed_load_config": "Не удалось загрузить конфиг:\n{error}",
            "config_dir_not_found": "Папка с конфигами не найдена: {path}",
            "invalid_atom_number": "Некорректное число в атоме: {error}",
            "failed_generate_pattern": "Не удалось построить дифрактограмму:\n{error}",
            "invalid_space_group": "Некорректная группа симметрии (номер Hall или пусто для авто): {value!r}",
            "invalid_second_wavelength": "Некорректная вторая длина волны: {value!r}",
            "invalid_ratio_nonnegative": "Отношение интенсивностей I(λ2)/I(λ1) должно быть неотрицательным.",
            "orthogonal_cell_title": "Ортогональная ячейка",
            "orthogonal_cell_warning": "Развёртка P/I/F/C/A/B задаётся в дробях по базису при α≈β≈γ≈90° (куб, тетрагон, орторомб и т.п.). Атомы не разворачиваются.",
            "plot_xlabel": "2θ (град)",
            "plot_ylabel": "Интенсивность, отн.ед.",
            "plot_title": "Дифрактограмма",
            "ratio_on_plot": "\nI(λ2)/I(λ1) = {ratio:g} (на графике)",
            "success_title": "Успех",
            "success_message": "Рассчитано для длин волн: {wl_msg}{ratio_msg}\nСохранено в {run_dir}: TXT и изображение для первой длины волны.",
            "window_title": "Расчёт дифрактограммы",
        },
        "en": {
            "config_frame": "Load data from list",
            "select_config": "List:",
            "refresh_list": "Refresh list",
            "add_config_file": "Add file…",
            "remove_config": "Remove from list",
            "add_config_file_title": "Select configuration file",
            "remove_config_confirm": "Remove «{name}» from the list?",
            "config_removed": "Removed «{name}» from the list.",
            "config_added": "Added: {path}",
            "config_add_failed": "Failed to add:\n{error}",
            "config_remove_failed": "Failed to remove:\n{error}",
            "config_nothing_selected": "Select an item from the list.",
            "config_invalid_path": "File or folder not found:\n{path}",
            "language": "Language:",
            "crystal_params": "Crystal Parameters",
            "centering": "Cell type:",
            "system": "Crystal system:",
            "name": "File name:",
            "element_col": "Element",
            "a_axis": "a (Å):",
            "b_axis": "b (Å):",
            "c_axis": "c (Å):",
            "alpha_angle": "α (°):",
            "beta_angle": "β (°):",
            "gamma_angle": "γ (°):",
            "atoms": "Atoms",
            "show_biso": "Show B_iso column",
            "add_atom": "Add Atom",
            "remove_atom": "Remove Last Atom",
            "pattern_params": "Pattern Parameters",
            "wavelength1": "Wavelength (Å):",
            "wavelength2": "Wavelength 2 (Å):",
            "wl2_ratio": "I(λ2)/I(λ1):",
            "tth_range": "2θ range:",
            "step": "step",
            "profile": "Profile:",
            "pseudo_voigt_eta": "η (pseudo-Voigt):",
            "caglioti": "Caglioti U, V, W:",
            "thetam": "θm (deg, polarization):",
            "use_wl2": "Use second wavelength",
            "generate_pattern": "Calculate diffractogram",
            "reset_zoom": "Restore initial zoom",
            "plot_area": "Diffractogram",
            "calc_results": "Calculated patterns",
            "save_to_folder": "Save to folder…",
            "save_pick_folder": "Choose folder to save",
            "save_files_group": "Files to save:",
            "save_file_txt": "Reflection table (.txt)",
            "save_file_json": "Reflections JSON (.json)",
            "save_file_powder_png": "Diffractogram (.png)",
            "save_file_cell_png": "Unit cell (.png)",
            "save_file_G_csv": "Metric G (.csv)",
            "save_file_Gstar_csv": "Metric G* (.csv)",
            "save_nothing_selected": "Select at least one file type.",
            "save_no_result_selected": "Select a pattern from the list.",
            "save_success": "Saved to:\n{path}",
            "save_failed": "Failed to save:\n{error}",
            "calc_done_message": (
                "Result added to the list on the right.\n"
                "Files saved under runs/{name}/\n"
                "Wavelengths: {wl_msg}{ratio_msg}"
            ),
            "label_reflection_angles": "Label 2θ angles",
            "label_reflection_angles_hkl": "Show angles and hkl",
            "hover_angle": "2θ = {angle:.3f}°",
            "print_pattern": "Print pattern",
            "warning_title": "Warning",
            "error_title": "Error",
            "input_error_title": "Input Error",
            "no_pattern_to_print": "Build a diffractogram first.",
            "printer_not_found": "No available system print backend was found.",
            "print_failed": "Failed to print:\n{error}",
            "print_sent": "Diffractogram was sent to printer.",
            "at_least_one_atom": "At least one atom required.",
            "failed_load_config": "Failed to load config:\n{error}",
            "config_dir_not_found": "Config directory not found: {path}",
            "invalid_atom_number": "Invalid number in atom: {error}",
            "failed_generate_pattern": "Failed to build diffractogram:\n{error}",
            "invalid_space_group": "Invalid space group (Hall number or empty for auto): {value!r}",
            "invalid_second_wavelength": "Invalid second wavelength: {value!r}",
            "invalid_ratio_nonnegative": "Intensity ratio I(λ2)/I(λ1) must be non-negative.",
            "orthogonal_cell_title": "Orthogonal cell",
            "orthogonal_cell_warning": "P/I/F/C/A/B expansion is defined in fractional shifts for basis with α≈β≈γ≈90° (cubic, tetragonal, orthorhombic, etc.). Atoms are not expanded.",
            "plot_xlabel": "2θ (deg)",
            "plot_ylabel": "Intensity, rel. units",
            "plot_title": "Diffractogram",
            "ratio_on_plot": "\nI(λ2)/I(λ1) = {ratio:g} (on plot)",
            "success_title": "Success",
            "success_message": "Calculated for wavelengths: {wl_msg}{ratio_msg}\nSaved under {run_dir}: TXT and image files for the first wavelength.",
            "window_title": "Diffractogram calculator",
        },
    }

    def __init__(self, root):
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
        self.bravais_centering_var = tk.StringVar(value="none")
        self.language_var = tk.StringVar(value="ru")
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
        self.profile_var = tk.StringVar(value=self.PROFILE_LABELS_BY_LANG["ru"]["bar"])
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
        self._profile_combo = None
        self._plot_outer = None
        self._plot_aspect = 1.25
        self._calc_results = []
        self._selected_calc_index = None
        self._calc_listbox = None
        self._save_option_vars = {}
        self._save_option_state_cache = {}
        self._plot_graph_frame = None
        self.input_width = 14
        self.input_font = ("TkDefaultFont", 12)
        self.label_font = ("TkDefaultFont", 12)

        self.create_widgets()
        self.scan_config_files()

    def tr(self, key: str) -> str:
        lang = self.language_var.get().strip().lower()
        return self.UI_TEXTS.get(lang, self.UI_TEXTS["en"]).get(key, key)

    @staticmethod
    def _configure_twotheta_axis(ax) -> None:
        """2θ: штрих каждый градус (без подписи), подписи каждые 10°."""
        ax.xaxis.set_major_locator(MultipleLocator(10))
        ax.xaxis.set_minor_locator(MultipleLocator(1))
        ax.tick_params(axis="x", which="major", length=6)
        ax.tick_params(axis="x", which="minor", length=3)

    def _lattice_label(self, key: str) -> str:
        lang = self.language_var.get().strip().lower()
        return self.LATTICE_FAMILY_LABELS_BY_LANG.get(
            lang, self.LATTICE_FAMILY_LABELS_BY_LANG["en"]
        ).get(key, key)

    def _lattice_labels(self):
        return [self._lattice_label(k) for k in self.LATTICE_FAMILY_KEYS]

    def _set_lattice_family_by_key(self, key: str):
        self.lattice_family_var.set(self._lattice_label(key))

    def _profile_label(self, key: str) -> str:
        lang = self.language_var.get().strip().lower()
        return self.PROFILE_LABELS_BY_LANG.get(
            lang, self.PROFILE_LABELS_BY_LANG["en"]
        ).get(key, key)

    def _profile_labels(self):
        return [self._profile_label(k) for k in self.PROFILE_KEYS]

    def _profile_key(self) -> str:
        label = self.profile_var.get().strip()
        for labels in self.PROFILE_LABELS_BY_LANG.values():
            for key, lbl in labels.items():
                if lbl == label:
                    return key
        return normalize_profile(label)

    def _set_profile_by_key(self, key: str):
        self.profile_var.set(self._profile_label(normalize_profile(key)))

    def _on_language_selected(self, _event=None):
        current_family = self._lattice_family_key()
        current_profile = self._profile_key()
        label_angles = self.label_angles_var.get()
        label_angles_hkl = self.label_angles_hkl_var.get()
        selected_calc = self._selected_calc_index
        self._save_option_state_cache = {
            k: v.get() for k, v in self._save_option_vars.items()
        }
        selected_config = (
            self.config_combo.get().strip() if hasattr(self, "config_combo") else ""
        )
        for child in self.root.winfo_children():
            child.destroy()
        self._section_content = {}
        self._section_buttons = {}
        self.create_widgets()
        self._set_lattice_family_by_key(current_family)
        self._set_profile_by_key(current_profile)
        self._on_profile_selected()
        self.label_angles_var.set(label_angles)
        self.label_angles_hkl_var.set(label_angles_hkl)
        self._selected_calc_index = selected_calc
        self._refresh_calc_results_list()
        if self._selected_calc_index is not None:
            self._select_calc_result_index(self._selected_calc_index, redraw=False)
            if self._calc_results:
                self._display_calc_result(self._calc_results[self._selected_calc_index])
        self.root.title(self.tr("window_title"))
        self.scan_config_files()
        if selected_config and selected_config in self.config_files:
            self.config_combo.set(selected_config)

    def find_config_dir(self):
        if getattr(sys, "frozen", False):
            return str(ensure_runtime_layout())
        rp = resource_path("config")
        if rp and os.path.isdir(rp):
            return rp
        if hasattr(sys, "_MEIPASS"):
            meipass_cfg = os.path.join(sys._MEIPASS, "config")
            if os.path.isdir(meipass_cfg):
                return meipass_cfg
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(script_dir, "config")
        if os.path.isdir(candidate):
            return candidate
        parent_dir = os.path.dirname(script_dir)
        candidate = os.path.join(parent_dir, "config")
        if os.path.isdir(candidate):
            return candidate
        return "config"

    def create_widgets(self):
        # tk.PanedWindow: есть minsize/paneconfigure; ttk.Panedwindow — другой API
        main_paned = tk.PanedWindow(self.root, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        self._main_paned = main_paned

        scroll_outer = ttk.Frame(main_paned)
        plot_outer = ttk.Frame(main_paned)
        self._plot_outer = plot_outer
        main_paned.add(scroll_outer, stretch="always", minsize=440)
        main_paned.add(plot_outer, stretch="always", minsize=360)

        plot_frame = ttk.LabelFrame(
            plot_outer, text=self.tr("plot_area"), padding=4
        )
        self._plot_graph_frame = plot_frame
        plot_frame.pack(fill=tk.BOTH, expand=True)

        scroll_canvas = tk.Canvas(scroll_outer, highlightthickness=0)
        vsb = ttk.Scrollbar(
            scroll_outer, orient="vertical", command=scroll_canvas.yview
        )
        scroll_canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._scroll_canvas = scroll_canvas

        self.form_container = ttk.Frame(scroll_canvas)
        inner_win = scroll_canvas.create_window(
            (0, 0), window=self.form_container, anchor="nw"
        )

        def _on_inner_configure(_event=None):
            scroll_canvas.configure(scrollregion=scroll_canvas.bbox("all"))

        def _on_scroll_canvas_configure(event):
            scroll_canvas.itemconfigure(inner_win, width=event.width)

        self.form_container.bind("<Configure>", _on_inner_configure)

        scroll_canvas.bind("<Configure>", _on_scroll_canvas_configure)

        def _on_mousewheel(event):
            if getattr(event, "num", None) == 4:
                scroll_canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                scroll_canvas.yview_scroll(1, "units")
            elif getattr(event, "delta", 0):
                scroll_canvas.yview_scroll(int(-event.delta / 120), "units")

        scroll_canvas.bind("<MouseWheel>", _on_mousewheel)
        scroll_canvas.bind("<Button-4>", _on_mousewheel)
        scroll_canvas.bind("<Button-5>", _on_mousewheel)
        self.form_container.bind("<MouseWheel>", _on_mousewheel)
        self.form_container.bind("<Button-4>", _on_mousewheel)
        self.form_container.bind("<Button-5>", _on_mousewheel)

        style = ttk.Style(self.root)
        style.configure("TLabel", font=self.label_font)
        style.configure("TButton", font=self.input_font)
        style.configure("TEntry", font=self.input_font)
        style.configure("TCombobox", font=self.input_font)
        style.configure("TLabelframe.Label", font=self.input_font)

        # Фрейм выбора конфига
        config_frame = ttk.LabelFrame(
            self.form_container, text=self.tr("config_frame"), padding=10
        )
        config_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(config_frame, text=self.tr("select_config")).grid(
            row=0, column=0, sticky="e", padx=5, pady=2
        )
        self.config_combo = ttk.Combobox(
            config_frame, state="readonly", width=self.input_width
        )
        self.config_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.config_combo.bind("<<ComboboxSelected>>", self.on_config_select)
        config_frame.grid_columnconfigure(1, weight=1)

        ttk.Button(
            config_frame, text=self.tr("refresh_list"), command=self.scan_config_files
        ).grid(row=0, column=2, padx=5, pady=2)

        config_btns = ttk.Frame(config_frame)
        config_btns.grid(row=1, column=0, columnspan=3, sticky="w", padx=5, pady=(4, 0))
        ttk.Button(
            config_btns,
            text=self.tr("add_config_file"),
            command=self._add_config_file_dialog,
        ).pack(side=tk.LEFT, padx=(0, 6))
        ttk.Button(
            config_btns,
            text=self.tr("remove_config"),
            command=self._remove_config_from_list,
        ).pack(side=tk.LEFT)

        # Кристаллографические параметры
        crystal_frame = ttk.LabelFrame(
            self.form_container, text=self.tr("crystal_params"), padding=10
        )
        crystal_frame.pack(fill="x", padx=10, pady=5)
        for c in range(4):
            crystal_frame.grid_columnconfigure(c, weight=1)

        row = 0
        name_row = ttk.Frame(crystal_frame)
        name_row.grid(row=row, column=0, columnspan=4, sticky="ew")
        name_inner = ttk.Frame(name_row)
        name_inner.pack(anchor="center", pady=2)
        ttk.Label(name_inner, text=self.tr("name")).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(name_inner, textvariable=self.name_var, width=self.input_width).pack(
            side=tk.LEFT
        )
        row += 1

        cell_mode_row = ttk.Frame(crystal_frame)
        cell_mode_row.grid(
            row=row, column=0, columnspan=4, sticky="ew", padx=5, pady=(4, 2)
        )
        cell_mode_inner = ttk.Frame(cell_mode_row)
        cell_mode_inner.pack(anchor="center")

        bravais_block = ttk.Frame(cell_mode_inner)
        bravais_block.pack(side=tk.LEFT, padx=(0, 28))
        ttk.Label(bravais_block, text=self.tr("centering")).pack(anchor="center")
        bravais_combo = ttk.Combobox(
            bravais_block,
            textvariable=self.bravais_centering_var,
            values=["none", "P", "I", "F", "C", "A", "B"],
            state="readonly",
            width=10,
        )
        bravais_combo.pack(anchor="center", pady=(4, 0))

        system_block = ttk.Frame(cell_mode_inner)
        system_block.pack(side=tk.LEFT)
        ttk.Label(system_block, text=self.tr("system")).pack(anchor="center")
        lattice_combo = ttk.Combobox(
            system_block,
            textvariable=self.lattice_family_var,
            values=self._lattice_labels(),
            state="readonly",
            width=28,
        )
        lattice_combo.pack(anchor="center", pady=(4, 0))
        lattice_combo.bind("<<ComboboxSelected>>", self._on_lattice_family_selected)
        row += 1

        self._cell_entries = {}
        ttk.Label(crystal_frame, text=self.tr("a_axis")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._cell_entries["a"] = ttk.Entry(
            crystal_frame, textvariable=self.a_var, width=self.input_width
        )
        self._cell_entries["a"].grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(crystal_frame, text=self.tr("alpha_angle")).grid(
            row=row, column=2, sticky="e", padx=(16, 5), pady=2
        )
        self._cell_entries["alpha"] = ttk.Entry(
            crystal_frame, textvariable=self.alpha_var, width=self.input_width
        )
        self._cell_entries["alpha"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text=self.tr("b_axis")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._cell_entries["b"] = ttk.Entry(
            crystal_frame, textvariable=self.b_var, width=self.input_width
        )
        self._cell_entries["b"].grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(crystal_frame, text=self.tr("beta_angle")).grid(
            row=row, column=2, sticky="e", padx=(16, 5), pady=2
        )
        self._cell_entries["beta"] = ttk.Entry(
            crystal_frame, textvariable=self.beta_var, width=self.input_width
        )
        self._cell_entries["beta"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text=self.tr("c_axis")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._cell_entries["c"] = ttk.Entry(
            crystal_frame, textvariable=self.c_var, width=self.input_width
        )
        self._cell_entries["c"].grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(crystal_frame, text=self.tr("gamma_angle")).grid(
            row=row, column=2, sticky="e", padx=(16, 5), pady=2
        )
        self._cell_entries["gamma"] = ttk.Entry(
            crystal_frame, textvariable=self.gamma_var, width=self.input_width
        )
        self._cell_entries["gamma"].grid(row=row, column=3, sticky="w", padx=5, pady=2)
        row += 1

        self._apply_lattice_constraints()

        # Таблица атомов (сворачиваемая секция)
        atoms_frame = self._create_collapsible_section(
            self.form_container, self.tr("atoms"), expanded=False
        )
        self.atoms_frame = atoms_frame

        atoms_tools = ttk.Frame(atoms_frame)
        atoms_tools.grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 4))
        ttk.Checkbutton(
            atoms_tools,
            text=self.tr("show_biso"),
            variable=self.show_biso_var,
            command=self._on_toggle_biso_column,
        ).pack(side=tk.LEFT)

        self.atom_widgets = []
        self._build_atom_headers(atoms_frame)
        self.refresh_atoms_table(atoms_frame)

        btn_frame = ttk.Frame(atoms_frame)
        btn_frame.grid(row=100, column=0, columnspan=5, pady=5)
        ttk.Button(btn_frame, text=self.tr("add_atom"), command=self.add_atom).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(
            btn_frame, text=self.tr("remove_atom"), command=self.remove_atom
        ).pack(side=tk.LEFT, padx=5)

        # Параметры дифракции (сворачиваемая секция)
        pattern_frame = self._create_collapsible_section(
            self.form_container, self.tr("pattern_params"), expanded=False
        )

        row = 0
        ttk.Label(pattern_frame, text=self.tr("wavelength1")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(
            pattern_frame, textvariable=self.wavelength_var, width=self.input_width
        ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Checkbutton(
            pattern_frame,
            text=self.tr("use_wl2"),
            variable=self.wavelength2_enabled_var,
            command=self._toggle_wavelength2_fields,
        ).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=2)
        row += 1

        self._wl2_fields_frame = ttk.Frame(pattern_frame)
        self._wl2_fields_frame.grid(row=row, column=0, columnspan=2, sticky="ew")
        self._wl2_fields_frame.grid_columnconfigure(1, weight=1)

        ttk.Label(self._wl2_fields_frame, text=self.tr("wavelength2")).grid(
            row=0, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(
            self._wl2_fields_frame,
            textvariable=self.wavelength2_var,
            width=self.input_width,
        ).grid(row=0, column=1, sticky="w", padx=5, pady=2)

        ttk.Label(self._wl2_fields_frame, text=self.tr("wl2_ratio")).grid(
            row=1, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(
            self._wl2_fields_frame,
            textvariable=self.wl2_intensity_ratio_var,
            width=self.input_width,
        ).grid(row=1, column=1, sticky="w", padx=5, pady=2)
        self._toggle_wavelength2_fields()
        row += 1

        ttk.Label(pattern_frame, text=self.tr("tth_range")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        range_frame = ttk.Frame(pattern_frame)
        range_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(range_frame, textvariable=self.tth_start_var, width=8).pack(
            side=tk.LEFT
        )
        ttk.Label(range_frame, text="—").pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.tth_end_var, width=8).pack(
            side=tk.LEFT
        )
        ttk.Label(range_frame, text=self.tr("step")).pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.tth_step_var, width=8).pack(
            side=tk.LEFT
        )
        row += 1

        ttk.Label(pattern_frame, text=self.tr("profile")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._profile_combo = ttk.Combobox(
            pattern_frame,
            textvariable=self.profile_var,
            values=self._profile_labels(),
            width=self.input_width,
        )
        self._profile_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        self._profile_combo.bind("<<ComboboxSelected>>", self._on_profile_selected)
        row += 1

        ttk.Label(pattern_frame, text=self.tr("pseudo_voigt_eta")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        self._eta_entry = ttk.Entry(
            pattern_frame, textvariable=self.eta_var, width=self.input_width
        )
        self._eta_entry.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text=self.tr("caglioti")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        caglioti_frame = ttk.Frame(pattern_frame)
        caglioti_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        for label, var in (("U", self.U_var), ("V", self.V_var), ("W", self.W_var)):
            ttk.Label(caglioti_frame, text=label).pack(side=tk.LEFT, padx=(0, 2))
            ttk.Entry(caglioti_frame, textvariable=var, width=10).pack(
                side=tk.LEFT, padx=(0, 8)
            )
        row += 1

        ttk.Label(pattern_frame, text=self.tr("thetam")).grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(
            pattern_frame, textvariable=self.thetam_deg_var, width=self.input_width
        ).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        self._on_profile_selected()

        actions_row = ttk.Frame(self.form_container)
        actions_row.pack(pady=10)
        ttk.Button(
            actions_row, text=self.tr("generate_pattern"), command=self.generate_pattern
        ).pack(side=tk.LEFT, padx=(0, 8))
        ttk.Button(
            actions_row, text=self.tr("reset_zoom"), command=self._reset_zoom
        ).pack(side=tk.LEFT)

        options_row = ttk.Frame(self.form_container)
        options_row.pack(anchor="w", padx=10, pady=(0, 6))
        ttk.Checkbutton(
            options_row,
            text=self.tr("label_reflection_angles"),
            variable=self.label_angles_var,
            command=self._on_label_angles_toggled,
        ).pack(side=tk.LEFT, padx=(0, 12))
        ttk.Checkbutton(
            options_row,
            text=self.tr("label_reflection_angles_hkl"),
            variable=self.label_angles_hkl_var,
            command=self._on_label_angles_hkl_toggled,
        ).pack(side=tk.LEFT)

        footer = ttk.Frame(self.form_container)
        footer.pack(fill="x", padx=10, pady=(2, 10))
        ttk.Separator(footer, orient="horizontal").pack(fill="x", pady=(2, 8))
        lang_row = ttk.Frame(footer)
        lang_row.pack(anchor="e")
        ttk.Label(lang_row, text=self.tr("language")).pack(side=tk.LEFT, padx=(0, 5))
        lang_combo = ttk.Combobox(
            lang_row,
            textvariable=self.language_var,
            values=list(self.LANGUAGE_LABELS.keys()),
            state="readonly",
            width=8,
        )
        lang_combo.pack(side=tk.LEFT)
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)
        ttk.Button(
            lang_row, text=self.tr("print_pattern"), command=self._print_pattern
        ).pack(side=tk.LEFT, padx=(12, 0))

        fig_h = 6.0
        fig_w = fig_h * self._plot_aspect
        self.figure = Figure(figsize=(fig_w, fig_h), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.ax.set_aspect("auto")
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        plot_frame.bind("<Configure>", self._resize_plot_figure)

        results_panel = ttk.LabelFrame(
            plot_outer, text=self.tr("calc_results"), padding=6
        )
        results_panel.pack(fill=tk.X, side=tk.BOTTOM, padx=2, pady=(4, 0))

        list_row = ttk.Frame(results_panel)
        list_row.pack(fill=tk.X, pady=(0, 4))
        list_scroll = ttk.Scrollbar(list_row, orient=tk.VERTICAL)
        self._calc_listbox = tk.Listbox(
            list_row,
            height=4,
            exportselection=False,
            yscrollcommand=list_scroll.set,
            font=self.input_font,
        )
        list_scroll.config(command=self._calc_listbox.yview)
        self._calc_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._calc_listbox.bind("<<ListboxSelect>>", self._on_calc_result_selected)

        save_opts = ttk.LabelFrame(
            results_panel, text=self.tr("save_files_group"), padding=4
        )
        save_opts.pack(fill=tk.X, pady=(0, 4))
        opts_inner = ttk.Frame(save_opts)
        opts_inner.pack(fill=tk.X)
        save_labels = {
            "txt": "save_file_txt",
            "json": "save_file_json",
            "powder_png": "save_file_powder_png",
            "cell_png": "save_file_cell_png",
            "G_csv": "save_file_G_csv",
            "Gstar_csv": "save_file_Gstar_csv",
        }
        self._save_option_vars = {}
        for col, key in enumerate(self.SAVE_OUTPUT_KEYS):
            var = tk.BooleanVar(
                value=self._save_option_state_cache.get(key, True)
            )
            self._save_option_vars[key] = var
            ttk.Checkbutton(
                opts_inner, text=self.tr(save_labels[key]), variable=var
            ).grid(row=col // 2, column=col % 2, sticky="w", padx=4, pady=1)

        ttk.Button(
            results_panel,
            text=self.tr("save_to_folder"),
            command=self._save_selected_result,
        ).pack(anchor="e")
        self._refresh_calc_results_list()
        self._zoom_selector = RectangleSelector(
            self.ax,
            self._on_zoom_select,
            useblit=True,
            button=[1],
            minspanx=0.05,
            minspany=0.05,
            spancoords="data",
            interactive=False,
        )
        self._zoom_reset_cid = self.canvas.mpl_connect(
            "button_press_event", self._on_zoom_reset_click
        )

        self.root.after_idle(self._set_initial_sash)

    def _on_zoom_select(self, eclick, erelease):
        if eclick.xdata is None or eclick.ydata is None:
            return
        if erelease.xdata is None or erelease.ydata is None:
            return
        x0, x1 = sorted((float(eclick.xdata), float(erelease.xdata)))
        if abs(x1 - x0) < 1e-6:
            return
        self.ax.set_xlim(x0, x1)
        self.tth_start_var.set(x0)
        self.tth_end_var.set(x1)
        self.canvas.draw_idle()

    def _on_zoom_reset_click(self, event):
        if event.inaxes != self.ax or event.button != 3:
            return
        self._reset_zoom()

    def _reset_zoom(self):
        if self._full_xlim is None or self._full_ylim is None:
            return
        self.ax.set_xlim(*self._full_xlim)
        self.tth_start_var.set(float(self._full_xlim[0]))
        self.tth_end_var.set(float(self._full_xlim[1]))
        self.canvas.draw_idle()

    def _print_pattern(self):
        if not self.ax.has_data():
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("no_pattern_to_print")
            )
            return

        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb", suffix=".png", delete=False
            ) as tmp:
                tmp_path = tmp.name
            self.figure.savefig(tmp_path, dpi=300, bbox_inches="tight")
            if os.name == "nt":
                # Windows: используем системный shell-print для зарегистрированного PNG viewer.
                os.startfile(tmp_path, "print")

                # Дадим spooler время прочитать файл перед удалением.
                def _cleanup_tmp(p):
                    try:
                        if os.path.exists(p):
                            os.remove(p)
                    except OSError:
                        pass

                self.root.after(120000, lambda p=tmp_path: _cleanup_tmp(p))
                tmp_path = None
            elif shutil.which("lp") is not None:
                subprocess.run(
                    ["lp", tmp_path], check=True, capture_output=True, text=True
                )
            elif shutil.which("lpr") is not None:
                subprocess.run(
                    ["lpr", tmp_path], check=True, capture_output=True, text=True
                )
            else:
                messagebox.showwarning(
                    self.tr("warning_title"), self.tr("printer_not_found")
                )
                return
            messagebox.showinfo(self.tr("success_title"), self.tr("print_sent"))
        except subprocess.CalledProcessError as e:
            msg = e.stderr.strip() if e.stderr else str(e)
            messagebox.showerror(
                self.tr("error_title"), self.tr("print_failed").format(error=msg)
            )
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"), self.tr("print_failed").format(error=str(e))
            )
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def _set_initial_sash(self):
        try:
            self._main_paned.update_idletasks()
            w = self._main_paned.winfo_width()
            if w > 300:
                left_width = max(440, min(int(w * 0.38), 680))
                self._main_paned.sashpos(0, left_width)
            self._resize_plot_figure()
        except (tk.TclError, AttributeError):
            pass

    def _resize_plot_figure(self, _event=None):
        frame = self._plot_graph_frame
        if frame is None:
            return
        try:
            pw = max(frame.winfo_width() - 12, 200)
            ph = max(frame.winfo_height() - 36, 160)
            dpi = self.figure.get_dpi()
            w_in = pw / dpi
            h_in = ph / dpi
            if w_in / h_in < self._plot_aspect:
                w_in = h_in * self._plot_aspect
            else:
                h_in = w_in / self._plot_aspect
            self.figure.set_size_inches(w_in, h_in, forward=True)
            self.figure.tight_layout(pad=1.0)
            self.canvas.draw_idle()
        except (tk.TclError, AttributeError, ValueError):
            pass

    def _toggle_wavelength2_fields(self):
        if self._wl2_fields_frame is None:
            return
        if self.wavelength2_enabled_var.get():
            self._wl2_fields_frame.grid()
        else:
            self._wl2_fields_frame.grid_remove()

    def _on_profile_selected(self, _event=None):
        if self._eta_entry is None:
            return
        state = "normal" if self._profile_key() == "pseudo-voigt" else "disabled"
        self._eta_entry.configure(state=state)

    def _create_collapsible_section(self, parent, title: str, expanded: bool = True):
        section = ttk.Frame(parent)
        section.pack(fill="x", padx=10, pady=5)

        btn = ttk.Button(
            section,
            command=lambda key=title: self._toggle_section(key),
        )
        btn.pack(fill="x")

        content = ttk.Frame(section, padding=10)
        if expanded:
            content.pack(fill="x", pady=(6, 0))

        self._section_buttons[title] = btn
        self._section_content[title] = content
        self._update_section_button_text(title)
        return content

    def _toggle_section(self, key: str):
        content = self._section_content.get(key)
        if content is None:
            return
        if content.winfo_manager():
            content.pack_forget()
        else:
            content.pack(fill="x", pady=(6, 0))
        self._update_section_button_text(key)

    def _update_section_button_text(self, key: str):
        btn = self._section_buttons.get(key)
        content = self._section_content.get(key)
        if btn is None or content is None:
            return
        marker = "▼" if content.winfo_manager() else "►"
        btn.configure(text=f"{marker} {key}")

    def _config_repo_root(self) -> str:
        if getattr(sys, "frozen", False):
            return str(application_directory())
        return os.path.dirname(self.config_dir) or "."

    def _user_config_dir(self) -> str:
        return self.config_dir

    def _config_list_meta_paths(self):
        d = self._user_config_dir()
        return (
            os.path.join(d, "extra_paths.txt"),
            os.path.join(d, "ignore_list.txt"),
            os.path.join(d, "list_entries.txt"),
        )

    @staticmethod
    def _normalize_config_path(raw: str, base: str) -> str:
        raw = raw.strip()
        if not raw:
            return ""
        if os.path.isabs(raw):
            return os.path.normpath(raw)
        return os.path.normpath(os.path.join(base, raw))

    def _path_for_list_entry_storage(self, path: str) -> str:
        path = os.path.normpath(os.path.abspath(path))
        base = self._config_repo_root()
        try:
            rel = os.path.relpath(path, base)
            if not rel.startswith(".."):
                return rel
        except ValueError:
            pass
        return path

    def _read_path_list_file(self, filepath: str) -> list[str]:
        if not os.path.isfile(filepath):
            return []
        base = self._config_repo_root()
        out = []
        with open(filepath, encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                p = self._normalize_config_path(raw, base)
                if p and (os.path.isfile(p) or os.path.isdir(p)):
                    out.append(p)
        return out

    def _load_config_extra_dirs(self):
        extra_paths_file, _, _ = self._config_list_meta_paths()
        return self._read_path_list_file(extra_paths_file)

    def _load_list_entries(self):
        seen = set()
        entries = []
        for path in (
            os.path.join(self._user_config_dir(), "list_entries.txt"),
            os.path.join(self.config_dir, "list_entries.txt"),
        ):
            for p in self._read_path_list_file(path):
                if p not in seen:
                    seen.add(p)
                    entries.append(p)
        return entries

    def _append_list_entry(self, path: str) -> None:
        path = os.path.normpath(os.path.abspath(path))
        if not os.path.isfile(path) and not os.path.isdir(path):
            raise FileNotFoundError(path)
        for existing in self._load_list_entries():
            if os.path.normpath(existing) == path:
                return
        user_dir = self._user_config_dir()
        os.makedirs(user_dir, exist_ok=True)
        list_file = os.path.join(user_dir, "list_entries.txt")
        store = self._path_for_list_entry_storage(path)
        need_newline = os.path.isfile(list_file) and os.path.getsize(list_file) > 0
        with open(list_file, "a", encoding="utf-8") as fh:
            if need_newline:
                fh.write("\n")
            fh.write(store + "\n")

    def _remove_list_entry_path(self, path: str) -> bool:
        path = os.path.normpath(os.path.abspath(path))
        list_file = os.path.join(self._user_config_dir(), "list_entries.txt")
        if not os.path.isfile(list_file):
            return False
        base = self._config_repo_root()
        kept = []
        removed = False
        with open(list_file, encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    kept.append(line if line.endswith("\n") else line + "\n")
                    continue
                p = self._normalize_config_path(raw, base)
                if p and os.path.normpath(p) == path:
                    removed = True
                    continue
                kept.append(line if line.endswith("\n") else line + "\n")
        if removed:
            with open(list_file, "w", encoding="utf-8") as fh:
                fh.writelines(kept)
        return removed

    def _load_config_ignore_patterns(self):
        patterns = []
        seen = set()
        user = self._user_config_dir()
        for path in (
            os.path.join(self.config_dir, "ignore_list.txt"),
            os.path.join(user, "ignore_list.txt"),
        ):
            if not os.path.isfile(path):
                continue
            with open(path, encoding="utf-8") as fh:
                for line in fh:
                    raw = line.strip()
                    if raw and not raw.startswith("#") and raw not in seen:
                        seen.add(raw)
                        patterns.append(raw)
        return patterns

    def _append_ignore_pattern(self, pattern: str) -> None:
        patterns = self._load_config_ignore_patterns()
        if pattern in patterns:
            return
        user_dir = self._user_config_dir()
        os.makedirs(user_dir, exist_ok=True)
        ignore_file = os.path.join(user_dir, "ignore_list.txt")
        with open(ignore_file, "a", encoding="utf-8") as fh:
            if os.path.isfile(ignore_file) and os.path.getsize(ignore_file) > 0:
                fh.write("\n")
            fh.write(pattern + "\n")

    def _remove_ignore_for_basename(self, basename: str) -> None:
        """Снять скрытие файла: убрать точные записи basename/stem из ignore_list."""
        stem = os.path.splitext(basename)[0]
        ignore_file = os.path.join(self._user_config_dir(), "ignore_list.txt")
        if not os.path.isfile(ignore_file):
            return
        kept = []
        changed = False
        with open(ignore_file, encoding="utf-8") as fh:
            for line in fh:
                raw = line.strip()
                if raw and not raw.startswith("#") and raw in (basename, stem):
                    changed = True
                    continue
                kept.append(line if line.endswith("\n") else line + "\n")
        if changed:
            with open(ignore_file, "w", encoding="utf-8") as fh:
                fh.writelines(kept)

    @staticmethod
    def _config_extensions():
        return (".txt", ".json", ".yaml", ".yml")

    def _is_config_file(self, path: str) -> bool:
        return os.path.isfile(path) and path.lower().endswith(self._config_extensions())

    def _register_config_file(self, filepath: str, into: dict) -> None:
        base = os.path.basename(filepath)
        ignore_patterns = self._load_config_ignore_patterns()
        if self._is_config_ignored(base, ignore_patterns):
            return
        name = os.path.splitext(base)[0]
        if name not in into:
            into[name] = filepath

    def _scan_config_dir(self, config_dir: str, into: dict) -> None:
        for ext in ("*.txt", "*.json", "*.yaml", "*.yml"):
            for f in sorted(glob.glob(os.path.join(config_dir, ext))):
                self._register_config_file(f, into)

    def _add_config_file_dialog(self):
        path = filedialog.askopenfilename(
            title=self.tr("add_config_file_title"),
            filetypes=[
                ("YAML/JSON", "*.yaml *.yml *.json *.txt"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        if not self._is_config_file(path):
            messagebox.showerror(
                self.tr("input_error_title"),
                self.tr("config_invalid_path").format(path=path),
            )
            return
        try:
            basename = os.path.basename(path)
            self._remove_ignore_for_basename(basename)
            self._append_list_entry(path)
            self.scan_config_files()
            stem = os.path.splitext(basename)[0]
            if stem in self.config_files:
                self.config_combo.set(stem)
                self.on_config_select()
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("config_added").format(path=path),
            )
        except OSError as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("config_add_failed").format(error=str(e)),
            )

    def _remove_config_from_list(self):
        name = self.config_combo.get().strip()
        if not name or name not in self.config_files:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("config_nothing_selected")
            )
            return
        if not messagebox.askyesno(
            self.tr("warning_title"),
            self.tr("remove_config_confirm").format(name=name),
        ):
            return
        filepath = os.path.normpath(os.path.abspath(self.config_files[name]))
        basename = os.path.basename(filepath)
        try:
            self._remove_list_entry_path(filepath)
            self._append_ignore_pattern(basename)
            self.scan_config_files()
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("config_removed").format(name=name),
            )
        except OSError as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("config_remove_failed").format(error=str(e)),
            )

    @staticmethod
    def _is_config_ignored(basename: str, patterns) -> bool:
        stem = os.path.splitext(basename)[0]
        meta = {
            "extra_paths.txt",
            "ignore_list.txt",
            "list_entries.txt",
        }
        if basename in meta:
            return True
        for pat in patterns:
            if fnmatch.fnmatch(basename, pat) or fnmatch.fnmatch(stem, pat):
                return True
        return False

    def _config_search_dirs(self):
        seen = set()
        dirs = []
        for d in [self.config_dir, *self._load_config_extra_dirs()]:
            d = os.path.normpath(d)
            if d not in seen and os.path.isdir(d):
                seen.add(d)
                dirs.append(d)
        return dirs

    def scan_config_files(self):
        self.config_files.clear()
        current = self.config_combo.get().strip()
        search_dirs = self._config_search_dirs()
        if not search_dirs and not self._load_list_entries():
            messagebox.showwarning(
                self.tr("warning_title"),
                self.tr("config_dir_not_found").format(path=self.config_dir),
            )
            self.config_combo["values"] = []
            return

        for config_dir in search_dirs:
            self._scan_config_dir(config_dir, self.config_files)

        for entry in self._load_list_entries():
            if os.path.isfile(entry):
                if self._is_config_file(entry):
                    self._register_config_file(entry, self.config_files)
            elif os.path.isdir(entry):
                self._scan_config_dir(entry, self.config_files)

        if self.config_files:
            names = sorted(self.config_files.keys(), key=str.lower)
            self.config_combo["values"] = names
            selected = None
            if current and current in self.config_files:
                selected = current
            else:
                for name in names:
                    if name.lower() == "cu":
                        selected = name
                        break
            if selected:
                self.config_combo.set(selected)
                filepath = self.config_files[selected]
                try:
                    config = self.parse_config_file(filepath)
                    self.apply_config(config)
                except Exception as e:
                    messagebox.showerror(
                        self.tr("error_title"),
                        self.tr("failed_load_config").format(error=str(e)),
                    )
            else:
                self.config_combo.set("")
        else:
            self.config_combo["values"] = []
            self.config_combo.set("")

    def on_config_select(self, event=None):
        selected = self.config_combo.get()
        if not selected or selected not in self.config_files:
            return
        filepath = self.config_files[selected]
        try:
            config = self.parse_config_file(filepath)
            self.apply_config(config)
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("failed_load_config").format(error=str(e)),
            )

    def parse_config_file(self, filepath):
        ext = os.path.splitext(filepath)[1].lower()
        if ext == ".json":
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        elif ext in (".yaml", ".yml"):
            with open(filepath, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        else:
            return self.parse_text_config(filepath)

    def parse_text_config(self, filepath):
        config = {}
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line or line.startswith("#"):
                i += 1
                continue
            if ":" in line:
                key, val = line.split(":", 1)
                key = key.strip()
                val = val.strip()
                if key == "atoms" and val.startswith("["):
                    atoms_str = val
                    i += 1
                    while i < len(lines) and not lines[i].strip().endswith("]"):
                        atoms_str += " " + lines[i].strip()
                        i += 1
                    if i < len(lines):
                        atoms_str += " " + lines[i].strip()
                    try:
                        import ast

                        atoms_list = ast.literal_eval(atoms_str)
                        config["atoms"] = atoms_list
                    except (SyntaxError, ValueError):
                        config["atoms"] = atoms_str
                else:
                    config[key] = self._parse_value(val)
            i += 1
        return config

    def _parse_value(self, val):
        v = val.strip()
        if v.lower() in ("true", "yes", "on"):
            return True
        if v.lower() in ("false", "no", "off"):
            return False
        try:
            if "." in v or "e" in v.lower():
                return float(v)
            else:
                return int(v)
        except ValueError:
            pass
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        return v

    def _synthesize_cell_params_from_family(self, fam: str | None, config: dict):
        """Дополняет a,b,c,α,β,γ по системе ячейки (как ограничения в GUI). В конфиге
        можно задать только независимые параметры; остальные берутся из config или текущих виджетов."""

        def cfg(key):
            if key in config and config[key] is not None:
                return float(config[key])
            return None

        def gv(var):
            try:
                return float(var.get())
            except tk.TclError:
                return None

        if not fam or fam == "manual":
            return

        if fam == "cubic":
            side = (
                cfg("a")
                or cfg("b")
                or cfg("c")
                or gv(self.a_var)
                or gv(self.b_var)
                or gv(self.c_var)
            )
            if side is None:
                return
            self.a_var.set(side)
            self.b_var.set(side)
            self.c_var.set(side)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(90.0)
            return

        if fam == "tetragonal":
            aa = cfg("a") or cfg("b") or gv(self.a_var) or gv(self.b_var)
            cc = cfg("c") or gv(self.c_var)
            if aa is None or cc is None:
                return
            self.a_var.set(aa)
            self.b_var.set(aa)
            self.c_var.set(cc)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(90.0)
            return

        if fam == "orthorhombic":
            a = cfg("a") or gv(self.a_var)
            b = cfg("b") or gv(self.b_var)
            c = cfg("c") or gv(self.c_var)
            if a is None or b is None or c is None:
                return
            self.a_var.set(a)
            self.b_var.set(b)
            self.c_var.set(c)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(90.0)
            return

        if fam == "hexagonal":
            aa = cfg("a") or cfg("b") or gv(self.a_var) or gv(self.b_var)
            cc = cfg("c") or gv(self.c_var)
            if aa is None or cc is None:
                return
            self.a_var.set(aa)
            self.b_var.set(aa)
            self.c_var.set(cc)
            self.alpha_var.set(90.0)
            self.beta_var.set(90.0)
            self.gamma_var.set(120.0)
            return

        if fam == "rhombohedral":
            side = (
                cfg("a")
                or cfg("b")
                or cfg("c")
                or gv(self.a_var)
                or gv(self.b_var)
                or gv(self.c_var)
            )
            ang = (
                cfg("alpha")
                or cfg("beta")
                or cfg("gamma")
                or gv(self.alpha_var)
                or gv(self.beta_var)
                or gv(self.gamma_var)
            )
            if side is None or ang is None:
                return
            self.a_var.set(side)
            self.b_var.set(side)
            self.c_var.set(side)
            self.alpha_var.set(ang)
            self.beta_var.set(ang)
            self.gamma_var.set(ang)
            return

        if fam == "monoclinic":
            a = cfg("a") or gv(self.a_var)
            b = cfg("b") or gv(self.b_var)
            c = cfg("c") or gv(self.c_var)
            if a is None or b is None or c is None:
                return
            self.a_var.set(a)
            self.b_var.set(b)
            self.c_var.set(c)
            self.alpha_var.set(90.0)
            self.gamma_var.set(90.0)
            be = cfg("beta")
            if be is not None:
                self.beta_var.set(be)

    def apply_config(self, config):
        if "name" in config:
            self.name_var.set(str(config["name"]))

        lf_key = None
        if "lattice_family" in config and config["lattice_family"] is not None:
            lf_key = str(config["lattice_family"]).strip().lower()
        elif "crystal_system" in config and config["crystal_system"] is not None:
            lf_key = str(config["crystal_system"]).strip().lower()
        if lf_key:
            if lf_key in self.LATTICE_FAMILY_KEYS:
                self._set_lattice_family_by_key(lf_key)

        if "a" in config and config["a"] is not None:
            self.a_var.set(float(config["a"]))
        if "b" in config and config["b"] is not None:
            self.b_var.set(float(config["b"]))
        if "c" in config and config["c"] is not None:
            self.c_var.set(float(config["c"]))
        if "alpha" in config and config["alpha"] is not None:
            self.alpha_var.set(float(config["alpha"]))
        if "beta" in config and config["beta"] is not None:
            self.beta_var.set(float(config["beta"]))
        if "gamma" in config and config["gamma"] is not None:
            self.gamma_var.set(float(config["gamma"]))

        self._synthesize_cell_params_from_family(lf_key, config)

        if "space_group" in config:
            if config["space_group"] is None:
                self.space_group_var.set("")
            else:
                self.space_group_var.set(str(int(config["space_group"])))

        if "atoms" in config and isinstance(config["atoms"], list):
            new_atoms = []
            for item in config["atoms"]:
                if len(item) >= 6:
                    atom = {
                        "element": str(item[0]),
                        "x": float(item[1]),
                        "y": float(item[2]),
                        "z": float(item[3]),
                        "occ": float(item[4]),
                        "biso": float(item[5]),
                    }
                    new_atoms.append(atom)
            if new_atoms:
                self.atoms = new_atoms
                self.refresh_atoms_table(self.atoms_frame)

        if "wavelength" in config:
            self.wavelength_var.set(float(config["wavelength"]))
        if "wavelength2" in config and config["wavelength2"] is not None:
            self.wavelength2_var.set(str(float(config["wavelength2"])))
            self.wavelength2_enabled_var.set(True)
        elif "wavelength_2" in config and config["wavelength_2"] is not None:
            self.wavelength2_var.set(str(float(config["wavelength_2"])))
            self.wavelength2_enabled_var.set(True)
        else:
            self.wavelength2_var.set("")
            self.wavelength2_enabled_var.set(False)
        if "wavelength2_intensity_ratio" in config:
            self.wl2_intensity_ratio_var.set(
                float(config["wavelength2_intensity_ratio"])
            )
        elif "wl2_intensity_ratio" in config:
            self.wl2_intensity_ratio_var.set(float(config["wl2_intensity_ratio"]))

        if (
            "twotheta_range" in config
            and isinstance(config["twotheta_range"], list)
            and len(config["twotheta_range"]) == 3
        ):
            self.tth_start_var.set(float(config["twotheta_range"][0]))
            self.tth_end_var.set(float(config["twotheta_range"][1]))
            self.tth_step_var.set(float(config["twotheta_range"][2]))

        if "U" in config:
            self.U_var.set(float(config["U"]))
        if "V" in config:
            self.V_var.set(float(config["V"]))
        if "W" in config:
            self.W_var.set(float(config["W"]))
        if "scale" in config:
            self.scale_var.set(float(config["scale"]))
        if "profile" in config:
            self._set_profile_by_key(str(config["profile"]))
        if "eta" in config:
            self.eta_var.set(float(config["eta"]))
        if "intensity_units" in config:
            self.intensity_units_var.set(str(config["intensity_units"]))
        if "normalize_intensity" in config:
            self.normalize_intensity_var.set(bool(config["normalize_intensity"]))
        if "intensity_max_value" in config:
            self.intensity_max_value_var.set(float(config["intensity_max_value"]))
        if "thetam_deg" in config:
            self.thetam_deg_var.set(float(config["thetam_deg"]))
        if "multiplicity_metric_rtol" in config:
            self.multiplicity_metric_rtol_var.set(
                float(config["multiplicity_metric_rtol"])
            )
        if "multiplicity_metric_atol" in config:
            self.multiplicity_metric_atol_var.set(
                float(config["multiplicity_metric_atol"])
            )
        _bravais_map = {
            "none": "none",
            "p": "none",
            "i": "I",
            "f": "F",
            "c": "C",
            "a": "A",
            "b": "B",
        }
        key = None
        if "bravais_centering" in config and config["bravais_centering"] is not None:
            key = "bravais_centering"
        elif "cubic_bravais" in config and config["cubic_bravais"] is not None:
            key = "cubic_bravais"
        if key is not None:
            v = str(config[key]).strip().lower()
            self.bravais_centering_var.set(_bravais_map.get(v, "none"))
        else:
            self.bravais_centering_var.set("none")

        if getattr(self, "_cell_entries", None):
            self._apply_lattice_constraints()
        self._toggle_wavelength2_fields()
        self._on_profile_selected()

    @staticmethod
    def _is_orthogonal_cell_approx_from_values(al, be, ga, atol_deg=0.5) -> bool:
        """α≈β≈γ≈90° — в такой базе задаются стандартные дробные сдвиги I/F/C/A/B."""
        return (
            abs(al - 90.0) < atol_deg
            and abs(be - 90.0) < atol_deg
            and abs(ga - 90.0) < atol_deg
        )

    def _lattice_family_key(self) -> str:
        cur = self.lattice_family_var.get()
        for k in self.LATTICE_FAMILY_KEYS:
            if self._lattice_label(k) == cur:
                return k
        return "manual"

    def _clear_lattice_traces(self):
        for var, tid in self._lattice_trace_ids:
            try:
                var.trace_remove("write", tid)
            except (tk.TclError, ValueError):
                pass
        self._lattice_trace_ids.clear()

    def _trace_write(self, var, callback):
        def _cb(*_):
            callback()

        tid = var.trace_add("write", _cb)
        self._lattice_trace_ids.append((var, tid))

    def _lock_cell_angle(self, which: str, value: float):
        E = self._cell_entries
        var_map = {
            "alpha": self.alpha_var,
            "beta": self.beta_var,
            "gamma": self.gamma_var,
        }
        self._lattice_sync_guard = True
        try:
            var_map[which].set(float(value))
        finally:
            self._lattice_sync_guard = False
        E[which].configure(state="disabled")

    def _sync_abc_equal(self):
        if self._lattice_sync_guard:
            return
        try:
            a = float(self.a_var.get())
        except (tk.TclError, ValueError):
            return
        self._lattice_sync_guard = True
        try:
            self.b_var.set(a)
            self.c_var.set(a)
        finally:
            self._lattice_sync_guard = False

    def _sync_b_from_a_only(self):
        if self._lattice_sync_guard:
            return
        try:
            a = float(self.a_var.get())
        except (tk.TclError, ValueError):
            return
        self._lattice_sync_guard = True
        try:
            self.b_var.set(a)
        finally:
            self._lattice_sync_guard = False

    def _sync_rhombo_angles_only(self):
        if self._lattice_sync_guard:
            return
        if self._lattice_family_key() != "rhombohedral":
            return
        try:
            al = float(self.alpha_var.get())
        except (tk.TclError, ValueError):
            return
        self._lattice_sync_guard = True
        try:
            self.beta_var.set(al)
            self.gamma_var.set(al)
        finally:
            self._lattice_sync_guard = False

    def _on_lattice_family_selected(self, event=None):
        self._apply_lattice_constraints()

    def _apply_lattice_constraints(self, event=None):
        self._clear_lattice_traces()
        E = self._cell_entries
        if not E:
            return
        for w in E.values():
            w.configure(state="normal")

        fam = self._lattice_family_key()
        if fam == "manual":
            return

        if fam in ("cubic", "tetragonal", "orthorhombic"):
            self._lock_cell_angle("alpha", 90.0)
            self._lock_cell_angle("beta", 90.0)
            self._lock_cell_angle("gamma", 90.0)
        elif fam == "hexagonal":
            self._lock_cell_angle("alpha", 90.0)
            self._lock_cell_angle("beta", 90.0)
            self._lock_cell_angle("gamma", 120.0)
        elif fam == "monoclinic":
            self._lock_cell_angle("alpha", 90.0)
            self._lock_cell_angle("gamma", 90.0)
        elif fam == "rhombohedral":
            try:
                al = float(self.alpha_var.get())
            except (tk.TclError, ValueError):
                al = 90.0
            self._lattice_sync_guard = True
            try:
                self.beta_var.set(al)
                self.gamma_var.set(al)
            finally:
                self._lattice_sync_guard = False
            E["beta"].configure(state="disabled")
            E["gamma"].configure(state="disabled")
            self._trace_write(self.alpha_var, self._sync_rhombo_angles_only)

        if fam in ("cubic", "rhombohedral"):
            self._sync_abc_equal()
            E["b"].configure(state="disabled")
            E["c"].configure(state="disabled")
            self._trace_write(self.a_var, self._sync_abc_equal)
        elif fam in ("tetragonal", "hexagonal"):
            self._sync_b_from_a_only()
            E["b"].configure(state="disabled")
            self._trace_write(self.a_var, self._sync_b_from_a_only)

    def _build_atom_headers(self, parent_frame):
        for w in self._atom_header_labels:
            w.destroy()
        self._atom_header_labels.clear()
        headers = [self.tr("element_col"), "x", "y", "z"]
        if self.show_biso_var.get():
            headers.append("Biso")
        for col, h in enumerate(headers):
            lab = ttk.Label(parent_frame, text=h, font=("Arial", 10, "bold"))
            lab.grid(row=1, column=col, padx=2, pady=2)
            self._atom_header_labels.append(lab)

    def _on_toggle_biso_column(self):
        synced = self.collect_atoms_from_widgets()
        if synced is not None:
            self.atoms = synced
        self._build_atom_headers(self.atoms_frame)
        self.refresh_atoms_table(self.atoms_frame)

    def refresh_atoms_table(self, parent_frame):
        for widgets in self.atom_widgets:
            for w in widgets:
                if w is not None:
                    w.destroy()
        self.atom_widgets.clear()

        data_row0 = 2
        for i, atom in enumerate(self.atoms):
            row = i + data_row0
            widgets = []

            entry_element = ttk.Entry(parent_frame, width=8)
            entry_element.grid(row=row, column=0, padx=2, pady=2)
            entry_element.insert(0, atom["element"])
            widgets.append(entry_element)

            entry_x = ttk.Entry(parent_frame, width=8)
            entry_x.grid(row=row, column=1, padx=2, pady=2)
            entry_x.insert(0, str(atom["x"]))
            widgets.append(entry_x)

            entry_y = ttk.Entry(parent_frame, width=8)
            entry_y.grid(row=row, column=2, padx=2, pady=2)
            entry_y.insert(0, str(atom["y"]))
            widgets.append(entry_y)

            entry_z = ttk.Entry(parent_frame, width=8)
            entry_z.grid(row=row, column=3, padx=2, pady=2)
            entry_z.insert(0, str(atom["z"]))
            widgets.append(entry_z)

            if self.show_biso_var.get():
                entry_biso = ttk.Entry(parent_frame, width=8)
                entry_biso.grid(row=row, column=4, padx=2, pady=2)
                entry_biso.insert(0, str(atom["biso"]))
                widgets.append(entry_biso)
            else:
                widgets.append(None)

            self.atom_widgets.append(widgets)

    def add_atom(self):
        atoms_data = self.collect_atoms_from_widgets()
        if atoms_data is None:
            return
        self.atoms = atoms_data
        self.atoms.append(
            {"element": "C", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.0}
        )
        self.refresh_atoms_table(self.atoms_frame)

    def remove_atom(self):
        if len(self.atoms) <= 1:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("at_least_one_atom")
            )
            return
        atoms_data = self.collect_atoms_from_widgets()
        if atoms_data is None:
            return
        self.atoms = atoms_data
        self.atoms.pop()
        self.refresh_atoms_table(self.atoms_frame)

    def collect_atoms_from_widgets(self):
        new_atoms = []
        for i, widgets in enumerate(self.atom_widgets):
            try:
                element = widgets[0].get()
                x = _parse_float_locale(widgets[1].get())
                y = _parse_float_locale(widgets[2].get())
                z = _parse_float_locale(widgets[3].get())
                if widgets[4] is not None:
                    biso = _parse_float_locale(widgets[4].get())
                else:
                    biso = float(self.atoms[i]["biso"])
                occ = float(self.atoms[i]["occ"])
                new_atoms.append(
                    {
                        "element": AtomicScatteringFactor.normalize_element_symbol(
                            element
                        ),
                        "x": x,
                        "y": y,
                        "z": z,
                        "occ": occ,
                        "biso": biso,
                    }
                )
            except ValueError as e:
                messagebox.showerror(
                    self.tr("input_error_title"),
                    self.tr("invalid_atom_number").format(error=e),
                )
                return None
        return new_atoms

    def _build_plot_peak_data(self, all_reflections, x, y_combined):
        peaks = []
        x0, x1 = float(x[0]), float(x[-1])
        for ref in all_reflections:
            xc = float(ref["twotheta"])
            if not (x0 <= xc <= x1):
                continue
            hkl = ref["hkl"]
            h, k, l_idx = (
                int(round(hkl[0])),
                int(round(hkl[1])),
                int(round(hkl[2])),
            )
            yp = float(np.interp(xc, x, y_combined))
            hkl_str = f"{h}{k}{l_idx}"
            peaks.append(
                {
                    "xc": xc,
                    "yp": yp,
                    "hkl": hkl_str,
                    "hover_hkl": hkl_str,
                    "hover_full": (
                        f"{hkl_str}\n" + self.tr("hover_angle").format(angle=xc)
                    ),
                    "angle_label": f"{xc:.2f}°",
                }
            )
        return peaks

    def _clear_peak_label_artists(self):
        for artist in self._peak_label_artists:
            try:
                if artist.axes is not None:
                    artist.remove()
            except (ValueError, AttributeError):
                pass
        self._peak_label_artists.clear()

    def _apply_reflection_label_mode(self):
        if self._plot_peak_data is None:
            return
        show_both = self.label_angles_hkl_var.get()
        show_angles = self.label_angles_var.get() and not show_both
        self._clear_peak_label_artists()
        self._hkl_hover_peaks = []
        labeled_angles = set()
        y_top = self.ax.get_ylim()[1]
        for peak in self._plot_peak_data:
            xc, yp = peak["xc"], peak["yp"]
            if show_both:
                y_text = min(yp * 1.02, y_top * 0.98) if yp > 0 else y_top * 0.05
                txt = self.ax.text(
                    xc,
                    y_text,
                    f"{peak['hkl']}\n{peak['angle_label']}",
                    fontsize=11,
                    ha="center",
                    va="bottom",
                    alpha=0.85,
                    clip_on=True,
                    zorder=5,
                )
                self._peak_label_artists.append(txt)
                self._hkl_hover_peaks.append((xc, yp, peak["hover_full"]))
            elif show_angles:
                self._hkl_hover_peaks.append((xc, yp, peak["hover_full"]))
                angle_key = round(xc, 3)
                if angle_key in labeled_angles:
                    continue
                labeled_angles.add(angle_key)
                y_text = min(yp * 1.02, y_top * 0.98) if yp > 0 else y_top * 0.05
                txt = self.ax.text(
                    xc,
                    y_text,
                    peak["angle_label"],
                    fontsize=11,
                    ha="center",
                    va="bottom",
                    alpha=0.85,
                    clip_on=True,
                    zorder=5,
                )
                self._peak_label_artists.append(txt)
            else:
                self._hkl_hover_peaks.append((xc, yp, peak["hover_full"]))
        self.canvas.draw_idle()

    def _on_label_angles_toggled(self):
        if self.label_angles_var.get():
            self.label_angles_hkl_var.set(False)
        self._apply_reflection_label_mode()

    def _on_label_angles_hkl_toggled(self):
        if self.label_angles_hkl_var.get():
            self.label_angles_var.set(False)
        self._apply_reflection_label_mode()

    def _hover_match_tolerance(self) -> float:
        x0, x1 = self.ax.get_xlim()
        return max(0.2, (float(x1) - float(x0)) * 0.015)

    def _on_hkl_hover_motion(self, event):
        ann = self._hkl_hover_annot
        if ann is None:
            return
        peaks = self._hkl_hover_peaks
        if not peaks:
            if ann.get_visible():
                ann.set_visible(False)
                self.canvas.draw_idle()
            return
        if event.inaxes != self.ax:
            if ann.get_visible():
                ann.set_visible(False)
                self.canvas.draw_idle()
            return
        mx = event.xdata
        if mx is None:
            return
        tol = self._hover_match_tolerance()
        best = None
        best_d = tol
        for xc, yp, lab in peaks:
            d = abs(mx - xc)
            if d < best_d:
                best_d = d
                best = (xc, yp, lab)
        if best is None:
            if ann.get_visible():
                ann.set_visible(False)
                self.canvas.draw_idle()
            return
        xc, yp, lab = best
        ann.xy = (xc, yp)
        ann.set_text(lab)
        ann.set_visible(True)
        self.canvas.draw_idle()

    def _format_calc_result_label(self, name: str, wavelengths, wl2_ratio: float) -> str:
        wl_part = ", ".join(f"{w:.4f} Å" for w in wavelengths)
        if len(wavelengths) > 1:
            wl_part += f"; I(λ2)/I(λ1)={wl2_ratio:g}"
        return f"{name} — {wl_part}"

    def _refresh_calc_results_list(self):
        if self._calc_listbox is None:
            return
        self._calc_listbox.delete(0, tk.END)
        for item in self._calc_results:
            self._calc_listbox.insert(tk.END, item["label"])

    def _select_calc_result_index(self, index: int, redraw: bool = True):
        if self._calc_listbox is None or index is None:
            return
        if index < 0 or index >= len(self._calc_results):
            return
        self._selected_calc_index = index
        self._calc_listbox.selection_clear(0, tk.END)
        self._calc_listbox.selection_set(index)
        self._calc_listbox.activate(index)
        if redraw:
            self._display_calc_result(self._calc_results[index])

    def _on_calc_result_selected(self, _event=None):
        if self._calc_listbox is None:
            return
        sel = self._calc_listbox.curselection()
        if not sel:
            return
        self._select_calc_result_index(int(sel[0]))

    def _get_selected_calc_result(self):
        if self._selected_calc_index is None:
            return None
        if self._selected_calc_index < 0 or self._selected_calc_index >= len(
            self._calc_results
        ):
            return None
        return self._calc_results[self._selected_calc_index]

    @staticmethod
    def _hkl_labels_on_curve(patterns, x, y):
        labels = []
        seen = set()
        for pattern in patterns:
            for hkl, xc, _ in pattern.hkl_labels:
                key = round(float(xc), 4)
                if key in seen:
                    continue
                seen.add(key)
                yp = float(np.interp(xc, x, y))
                labels.append((hkl, float(xc), yp))
        return labels

    def _display_calc_result(self, result: dict):
        x = result["x"]
        y = result["y"]
        all_reflections = result["all_reflections"]
        angle_values = sorted(
            {
                ref["twotheta"]
                for ref in all_reflections
                if x[0] <= ref["twotheta"] <= x[-1]
            }
        )
        self.ax.clear()
        self._peak_label_artists.clear()
        self.ax.plot(x, y, linewidth=1.3)
        self.ax.set_xlabel(self.tr("plot_xlabel"), fontsize=14)
        self.ax.set_ylabel(self.tr("plot_ylabel"), fontsize=14)
        self.ax.set_title(self.tr("plot_title"), fontsize=15)
        self.ax.tick_params(axis="both", labelsize=11)
        self._configure_twotheta_axis(self.ax)
        self.ax.grid(True, axis="x", which="major", linewidth=0.6, alpha=0.45)
        self.ax.grid(True, axis="x", which="minor", linewidth=0.35, alpha=0.25)
        y_top = float(np.max(y)) if len(y) else 1.0
        self._plot_peak_data = self._build_plot_peak_data(all_reflections, x, y)
        self._hkl_hover_peaks = []
        x_right = float(x[-1])
        self.ax.set_xlim(0.0, x_right)
        if self._hkl_hover_annot is None:
            self._hkl_hover_annot = self.ax.annotate(
                "",
                xy=(0, 0),
                xytext=(0, 24),
                textcoords="offset points",
                ha="center",
                va="bottom",
                bbox=dict(boxstyle="round,pad=0.35", fc="wheat", alpha=0.92),
                fontsize=11,
                visible=False,
                zorder=10,
            )
            if self._hkl_hover_cid is not None:
                self.canvas.mpl_disconnect(self._hkl_hover_cid)
            self._hkl_hover_cid = self.canvas.mpl_connect(
                "motion_notify_event", self._on_hkl_hover_motion
            )
        self.ax.set_ylim(bottom=0.0, top=(y_top * 1.08 if y_top > 0 else 1.0))
        self.ax.margins(x=0)
        self._apply_reflection_label_mode()
        if angle_values:
            self.ax.vlines(
                angle_values,
                [0.0] * len(angle_values),
                [float(np.interp(a, x, y)) for a in angle_values],
                colors="gray",
                linewidth=0.4,
                alpha=0.35,
                zorder=2,
            )
        self._full_xlim = (0.0, x_right)
        self._full_ylim = tuple(self.ax.get_ylim())
        self.figure.tight_layout(pad=1.2)
        self.canvas.draw()

    def _append_calc_result(
        self,
        name: str,
        patterns,
        wl2_ratio: float,
        x,
        y,
        all_reflections,
        wavelengths,
    ):
        result = {
            "label": self._format_calc_result_label(name, wavelengths, wl2_ratio),
            "name": name,
            "patterns": patterns,
            "wl2_ratio": wl2_ratio,
            "x": x,
            "y": y,
            "all_reflections": all_reflections,
            "wavelengths": list(wavelengths),
        }
        self._calc_results.append(result)
        self._refresh_calc_results_list()
        self._select_calc_result_index(len(self._calc_results) - 1)

    def _runs_output_dir(self, base_name: str) -> Path:
        if getattr(sys, "frozen", False):
            root = application_directory()
        else:
            root = Path.cwd()
        return root / "runs" / base_name

    def _autosave_calc_result_to_runs(self, result: dict) -> None:
        options = {key: True for key in self.SAVE_OUTPUT_KEYS}
        dest = self._runs_output_dir(result["name"])
        try:
            self._export_calc_result(result, str(dest), options)
        except OSError:
            pass

    def _export_calc_result(self, result: dict, dest_dir: str, options: dict) -> None:
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        base_name = result["name"]
        patterns = result["patterns"]
        crystal = patterns[0].crystal

        if options.get("txt"):
            for pattern in patterns:
                pattern.write_reflections_txt(dest / f"{pattern.name}.txt")
        if options.get("json"):
            for pattern in patterns:
                pattern.write_reflections_json(dest / f"{pattern.name}.json")
        if options.get("G_csv"):
            np.savetxt(dest / "G.csv", crystal.G, delimiter=",")
        if options.get("Gstar_csv"):
            np.savetxt(dest / "Gstar.csv", crystal.Gstar, delimiter=",")
        if options.get("cell_png"):
            crystal.save_image(filename=dest / f"{base_name}.png")
        if options.get("powder_png"):
            hkl_plot = self._hkl_labels_on_curve(patterns, result["x"], result["y"])
            Plot.save_powder_png(
                dest / f"{base_name}_powder.png",
                result["x"],
                result["y"],
                hkl_plot,
                base_name,
            )

    def _save_selected_result(self):
        result = self._get_selected_calc_result()
        if result is None:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("save_no_result_selected")
            )
            return
        options = {k: v.get() for k, v in self._save_option_vars.items()}
        if not any(options.values()):
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("save_nothing_selected")
            )
            return
        dest = filedialog.askdirectory(
            title=self.tr("save_pick_folder"), mustexist=False
        )
        if not dest:
            return
        try:
            self._export_calc_result(result, dest, options)
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("save_success").format(path=dest),
            )
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"), self.tr("save_failed").format(error=str(e))
            )

    def generate_pattern(self):
        try:
            atoms_data = self.collect_atoms_from_widgets()
            if atoms_data is None:
                return

            atom_objects = [
                Atom(
                    atom["element"],
                    atom["x"],
                    atom["y"],
                    atom["z"],
                    atom["occ"],
                    atom["biso"],
                )
                for atom in atoms_data
            ]

            sg_text = self.space_group_var.get().strip()
            if sg_text == "" or sg_text.lower() in ("auto", "null", "none"):
                spacegroup_number = None
            else:
                try:
                    spacegroup_number = int(sg_text)
                except ValueError:
                    messagebox.showerror(
                        self.tr("input_error_title"),
                        self.tr("invalid_space_group").format(value=sg_text),
                    )
                    return

            bravais = self.bravais_centering_var.get().strip().lower()
            if bravais == "p":
                bravais = "none"

            a = _safe_double_get(self.a_var, "a (Å)")
            b = _safe_double_get(self.b_var, "b (Å)")
            c = _safe_double_get(self.c_var, "c (Å)")
            alpha = _safe_double_get(self.alpha_var, "α (deg)")
            beta = _safe_double_get(self.beta_var, "β (deg)")
            gamma = _safe_double_get(self.gamma_var, "γ (deg)")
            if None in (a, b, c, alpha, beta, gamma):
                return

            if spacegroup_number is None and bravais not in ("", "none"):
                if not self._is_orthogonal_cell_approx_from_values(alpha, beta, gamma):
                    messagebox.showwarning(
                        self.tr("orthogonal_cell_title"),
                        self.tr("orthogonal_cell_warning"),
                    )
                else:
                    atom_objects = expand_atoms_bravais_centering(
                        atom_objects, bravais.upper()
                    )

            crystal = Crystal(
                a,
                b,
                c,
                alpha,
                beta,
                gamma,
                asf=self.asf,
                spacegroup_number=spacegroup_number,
                atoms=atom_objects,
            )

            tth_s = _safe_double_get(self.tth_start_var, "2θ start")
            tth_e = _safe_double_get(self.tth_end_var, "2θ end")
            tth_step = _safe_double_get(self.tth_step_var, "2θ step")
            if None in (tth_s, tth_e, tth_step):
                return
            tth_range = np.array([tth_s, tth_e, tth_step])
            intensity_min = 1e-6

            wl = _safe_double_get(self.wavelength_var, "wavelength")
            wl2_text = (
                self.wavelength2_var.get().strip()
                if self.wavelength2_enabled_var.get()
                else ""
            )
            wl2 = None
            if wl2_text:
                try:
                    wl2 = _parse_float_locale(wl2_text)
                    if wl2 <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showerror(
                        self.tr("input_error_title"),
                        self.tr("invalid_second_wavelength").format(value=wl2_text),
                    )
                    return
            thetam = _safe_double_get(self.thetam_deg_var, "θ_m")
            U = _safe_double_get(self.U_var, "U")
            V = _safe_double_get(self.V_var, "V")
            W = _safe_double_get(self.W_var, "W")
            scale = _safe_double_get(self.scale_var, "scale")
            eta = _safe_double_get(self.eta_var, "η")
            imax = _safe_double_get(self.intensity_max_value_var, "intensity max")
            mm_rtol = _safe_double_get(
                self.multiplicity_metric_rtol_var, "multiplicity rtol"
            )
            mm_atol = _safe_double_get(
                self.multiplicity_metric_atol_var, "multiplicity atol"
            )
            if None in (
                wl,
                thetam,
                U,
                V,
                W,
                scale,
                eta,
                imax,
                mm_rtol,
                mm_atol,
            ):
                return

            wavelengths = [wl]
            wl2_ratio = 1.0
            if wl2 is not None:
                wavelengths.append(wl2)
                wl2_ratio = _safe_double_get(
                    self.wl2_intensity_ratio_var, "I(λ2)/I(λ1)"
                )
                if wl2_ratio is None:
                    return
                if wl2_ratio < 0:
                    messagebox.showerror(
                        self.tr("input_error_title"),
                        self.tr("invalid_ratio_nonnegative"),
                    )
                    return

            patterns = []
            for idx, wli in enumerate(wavelengths, start=1):
                suffix = "" if idx == 1 else f"_wl{idx}"
                pattern_i = PowderPattern(
                    f"{self.name_var.get()}{suffix}",
                    crystal,
                    wli,
                    tth_range,
                    thetam_deg=thetam,
                    U=U,
                    V=V,
                    W=W,
                    scale=scale,
                    profile=self._profile_key(),
                    eta=eta,
                    intensity_units=self.intensity_units_var.get(),
                    normalize_intensity=self.normalize_intensity_var.get(),
                    intensity_max_value=imax,
                    intensity_min=intensity_min,
                    multiplicity_mode="metric",
                    multiplicity_metric_rtol=mm_rtol,
                    multiplicity_metric_atol=mm_atol,
                )
                patterns.append(pattern_i)

            x, y = patterns[0].get_pattern_data()
            y_combined = np.array(y, copy=True)
            all_reflections = list(patterns[0].reflections)
            for p in patterns[1:]:
                xp, yp = p.get_pattern_data()
                yp_scaled = wl2_ratio * np.asarray(yp, dtype=float)
                if len(xp) == len(x) and np.allclose(xp, x):
                    y_combined += yp_scaled
                else:
                    y_combined += np.interp(x, xp, yp_scaled)
                all_reflections.extend(p.reflections)

            base_name = self.name_var.get().strip() or "pattern"
            self._append_calc_result(
                base_name,
                patterns,
                wl2_ratio,
                x,
                y_combined,
                all_reflections,
                wavelengths,
            )
            self._autosave_calc_result_to_runs(self._calc_results[-1])
            wl_msg = ", ".join(f"{w:.4f} Å" for w in wavelengths)
            ratio_msg = (
                self.tr("ratio_on_plot").format(ratio=wl2_ratio)
                if wl2 is not None
                else ""
            )
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("calc_done_message").format(
                    name=base_name,
                    wl_msg=wl_msg,
                    ratio_msg=ratio_msg,
                ),
            )
        except Exception as e:
            messagebox.showerror(
                self.tr("error_title"),
                self.tr("failed_generate_pattern").format(error=str(e)),
            )


if __name__ == "__main__":
    root = tk.Tk()
    app = PowderPatternGUI(root)
    root.mainloop()
