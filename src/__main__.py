import glob
import json
import locale
import os
import sys

# До import tkinter: на Windows с LC_NUMERIC≠C виджеты DoubleVar/ввод часто ломаются (запятая vs точка).
try:
    locale.setlocale(locale.LC_NUMERIC, "C")
except (locale.Error, OSError):
    pass

import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import yaml
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from .model.atom.atom import Atom, AtomicScatteringFactor
from .model.crystal.crystal import Crystal
from .model.crystal.utils import expand_atoms_bravais_centering
from .model.pattern.plot import Plot
from .model.pattern.powder import PowderPattern
from .runtime_layout import resource_path

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
    def __init__(self, root):
        self.root = root
        self.root.title("Powder Pattern Generator")
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
        # P/I/F/C/A/B — развёртка по центрированию (дроби ячейки) при Hall пусто
        self.bravais_centering_var = tk.StringVar(value="none")

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
        self.tth_start_var = tk.DoubleVar(value=20.0)
        self.tth_end_var = tk.DoubleVar(value=100.0)
        self.tth_step_var = tk.DoubleVar(value=0.02)

        self.U_var = tk.DoubleVar(value=0.01)
        self.V_var = tk.DoubleVar(value=-0.005)
        self.W_var = tk.DoubleVar(value=0.005)
        self.scale_var = tk.DoubleVar(value=1.0)
        self.profile_var = tk.StringVar(value="stick")
        self.eta_var = tk.DoubleVar(value=0.5)
        self.intensity_units_var = tk.StringVar(value="arbitrary")
        self.normalize_intensity_var = tk.BooleanVar(value=True)
        self.intensity_max_value_var = tk.DoubleVar(value=100.0)
        self.thetam_deg_var = tk.DoubleVar(value=0.0)
        self.intensity_min_var = tk.StringVar(value="1e-6")
        self.multiplicity_mode_var = tk.StringVar(value="metric")
        self.multiplicity_metric_rtol_var = tk.DoubleVar(value=1e-7)
        self.multiplicity_metric_atol_var = tk.DoubleVar(value=1e-12)

        self.config_dir = self.find_config_dir()
        asf_path = self.find_asf_data_path()
        self.asf = AtomicScatteringFactor(asf_path)
        self.config_files = {}
        self.atoms_frame = None

        self.create_widgets()
        self.scan_config_files()

    def find_config_dir(self):
        rp = resource_path("config")
        if rp and os.path.isdir(rp):
            return rp
        # PyInstaller onefile: не полагаться только на __file__ (иногда отличается от _MEIPASS).
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
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

    def find_asf_data_path(self):
        rp = resource_path("data", "f0_WaasKirf.dat")
        if rp and os.path.isfile(rp):
            return rp
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            meipass_dat = os.path.join(sys._MEIPASS, "data", "f0_WaasKirf.dat")
            if os.path.isfile(meipass_dat):
                return meipass_dat
        script_dir = os.path.dirname(os.path.abspath(__file__))
        candidate = os.path.join(script_dir, "data", "f0_WaasKirf.dat")
        if os.path.isfile(candidate):
            return candidate
        parent_dir = os.path.dirname(script_dir)
        candidate = os.path.join(parent_dir, "data", "f0_WaasKirf.dat")
        if os.path.isfile(candidate):
            return candidate
        return os.path.join(script_dir, "data", "f0_WaasKirf.dat")

    def create_widgets(self):
        # tk.PanedWindow: есть minsize/paneconfigure; ttk.Panedwindow — другой API
        main_paned = tk.PanedWindow(self.root, orient=tk.VERTICAL)
        main_paned.pack(fill=tk.BOTH, expand=True)
        self._main_paned = main_paned

        scroll_outer = ttk.Frame(main_paned)
        plot_outer = ttk.Frame(main_paned)
        main_paned.add(scroll_outer, stretch="always")
        main_paned.add(plot_outer, stretch="always", minsize=280)

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

        # Фрейм выбора конфига
        config_frame = ttk.LabelFrame(
            self.form_container, text="Load Default Crystal", padding=10
        )
        config_frame.pack(fill="x", padx=10, pady=5)
        config_frame.columnconfigure(1, weight=1)

        ttk.Label(config_frame, text="Select config:").grid(
            row=0, column=0, sticky="e", padx=5, pady=2
        )
        self.config_combo = ttk.Combobox(config_frame, state="readonly")
        self.config_combo.grid(row=0, column=1, sticky="ew", padx=5, pady=2)
        self.config_combo.bind("<<ComboboxSelected>>", self.on_config_select)

        ttk.Button(
            config_frame, text="Refresh list", command=self.scan_config_files
        ).grid(row=0, column=2, padx=5, pady=2)

        # Кристаллографические параметры
        crystal_frame = ttk.LabelFrame(
            self.form_container, text="Crystal Parameters", padding=10
        )
        crystal_frame.pack(fill="x", padx=10, pady=5)
        crystal_frame.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(crystal_frame, text="Name:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.name_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="a (Å):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.a_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="b (Å):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.b_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="c (Å):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.c_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="α (°):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.alpha_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="β (°):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.beta_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="γ (°):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.gamma_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(crystal_frame, text="Space group (Hall, пусто=auto):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.space_group_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(
            crystal_frame,
            text="Центрир. Bravais (если Hall пусто):",
        ).grid(row=row, column=0, sticky="e", padx=5, pady=2)
        bravais_combo = ttk.Combobox(
            crystal_frame,
            textvariable=self.bravais_centering_var,
            values=["none", "P", "I", "F", "C", "A", "B"],
            state="readonly",
            width=8,
        )
        bravais_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Label(
            crystal_frame,
            text="α≈β≈γ≈90°: P/I/F/C/A/B в долях a,b,c",
            font=("TkDefaultFont", 8),
        ).grid(row=row, column=2, sticky="w", padx=4, pady=2)
        row += 1

        # Таблица атомов
        atoms_frame = ttk.LabelFrame(self.form_container, text="Atoms", padding=10)
        atoms_frame.pack(fill="x", padx=10, pady=5)
        self.atoms_frame = atoms_frame

        headers = ["Element", "x", "y", "z", "Occupancy", "Biso"]
        for col, h in enumerate(headers):
            ttk.Label(atoms_frame, text=h, font=("Arial", 10, "bold")).grid(
                row=0, column=col, padx=2, pady=2
            )

        self.atom_widgets = []
        self.refresh_atoms_table(atoms_frame)

        btn_frame = ttk.Frame(atoms_frame)
        btn_frame.grid(row=100, column=0, columnspan=6, pady=5)
        ttk.Button(btn_frame, text="Add Atom", command=self.add_atom).pack(
            side=tk.LEFT, padx=5
        )
        ttk.Button(btn_frame, text="Remove Last Atom", command=self.remove_atom).pack(
            side=tk.LEFT, padx=5
        )

        # Параметры дифракции
        pattern_frame = ttk.LabelFrame(
            self.form_container, text="Pattern Parameters", padding=10
        )
        pattern_frame.pack(fill="x", padx=10, pady=5)
        pattern_frame.columnconfigure(1, weight=1)

        row = 0
        ttk.Label(pattern_frame, text="Wavelength (Å):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.wavelength_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="2θ range (start, end, step):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        range_frame = ttk.Frame(pattern_frame)
        range_frame.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        ttk.Entry(range_frame, textvariable=self.tth_start_var, width=8).pack(
            side=tk.LEFT
        )
        ttk.Label(range_frame, text="—").pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.tth_end_var, width=8).pack(
            side=tk.LEFT
        )
        ttk.Label(range_frame, text="step").pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.tth_step_var, width=8).pack(
            side=tk.LEFT
        )
        row += 1

        ttk.Label(pattern_frame, text="U:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.U_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="V:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.V_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="W:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.W_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Scale:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.scale_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Profile:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        profile_combo = ttk.Combobox(
            pattern_frame,
            textvariable=self.profile_var,
            values=["stick", "gaussian", "lorentzian", "pseudo-voigt"],
        )
        profile_combo.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Eta (for pseudo-voigt):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.eta_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Intensity units:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.intensity_units_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Normalize intensity:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Checkbutton(pattern_frame, variable=self.normalize_intensity_var).grid(
            row=row, column=1, sticky="w", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Max intensity value:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.intensity_max_value_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="θm (deg, polarization):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.thetam_deg_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Intensity cutoff (min):").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(pattern_frame, textvariable=self.intensity_min_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
        row += 1

        ttk.Label(pattern_frame, text="Multiplicity:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        mult_combo = ttk.Combobox(
            pattern_frame,
            textvariable=self.multiplicity_mode_var,
            values=["symmetry", "metric"],
            state="readonly",
            width=18,
        )
        mult_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Metric mult. rtol / atol:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        mult_tol = ttk.Frame(pattern_frame)
        mult_tol.grid(row=row, column=1, sticky="ew", padx=5, pady=2)
        ttk.Entry(
            mult_tol, textvariable=self.multiplicity_metric_rtol_var, width=12
        ).pack(side=tk.LEFT)
        ttk.Entry(
            mult_tol, textvariable=self.multiplicity_metric_atol_var, width=12
        ).pack(side=tk.LEFT, padx=(8, 0))
        row += 1

        ttk.Button(
            self.form_container, text="Generate Pattern", command=self.generate_pattern
        ).pack(pady=10)

        sh = self.root.winfo_screenheight()
        sw = self.root.winfo_screenwidth()
        fig_w = max(6.0, min(16.0, (sw - 80) / 100))
        fig_h = max(5.5, min(9.0, (sh - 220) / 100))
        self.figure = Figure(figsize=(fig_w, fig_h), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=plot_outer)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self.root.after_idle(self._set_initial_sash)

    def _set_initial_sash(self):
        try:
            self._main_paned.update_idletasks()
            h = self._main_paned.winfo_height()
            if h > 120:
                self._main_paned.sashpos(0, min(int(h * 0.40), 650))
        except (tk.TclError, AttributeError):
            pass

    def scan_config_files(self):
        self.config_files.clear()
        if not os.path.isdir(self.config_dir):
            messagebox.showwarning(
                "Warning", f"Config directory not found: {self.config_dir}"
            )
            self.config_combo["values"] = []
            return

        extensions = ["*.txt", "*.json", "*.yaml", "*.yml"]
        files = []
        for ext in extensions:
            files.extend(glob.glob(os.path.join(self.config_dir, ext)))

        for f in files:
            name = os.path.splitext(os.path.basename(f))[0]
            self.config_files[name] = f

        if self.config_files:
            self.config_combo["values"] = list(self.config_files.keys())
        else:
            self.config_combo["values"] = []

    def on_config_select(self, event):
        selected = self.config_combo.get()
        if not selected or selected not in self.config_files:
            return
        filepath = self.config_files[selected]
        try:
            config = self.parse_config_file(filepath)
            self.apply_config(config)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config:\n{str(e)}")

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
                    except:
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
        except:
            pass
        if v.startswith('"') and v.endswith('"'):
            return v[1:-1]
        if v.startswith("'") and v.endswith("'"):
            return v[1:-1]
        return v

    def apply_config(self, config):
        if "name" in config:
            self.name_var.set(str(config["name"]))
        if "a" in config:
            self.a_var.set(float(config["a"]))
        if "b" in config:
            self.b_var.set(float(config["b"]))
        if "c" in config:
            self.c_var.set(float(config["c"]))
        if "alpha" in config:
            self.alpha_var.set(float(config["alpha"]))
        if "beta" in config:
            self.beta_var.set(float(config["beta"]))
        if "gamma" in config:
            self.gamma_var.set(float(config["gamma"]))
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
            self.profile_var.set(str(config["profile"]))
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
        if "intensity_min" in config and config["intensity_min"] is not None:
            self.intensity_min_var.set(str(float(config["intensity_min"])))
        else:
            self.intensity_min_var.set("1e-6")
        if "multiplicity_mode" in config:
            self.multiplicity_mode_var.set(str(config["multiplicity_mode"]).lower())
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
            "p": "P",
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

    @staticmethod
    def _is_orthogonal_cell_approx_from_values(al, be, ga, atol_deg=0.5) -> bool:
        """α≈β≈γ≈90° — в такой базе задаются стандартные дробные сдвиги I/F/C/A/B."""
        return (
            abs(al - 90.0) < atol_deg
            and abs(be - 90.0) < atol_deg
            and abs(ga - 90.0) < atol_deg
        )

    def refresh_atoms_table(self, parent_frame):
        for widgets in self.atom_widgets:
            for w in widgets:
                w.destroy()
        self.atom_widgets.clear()

        for i, atom in enumerate(self.atoms):
            row = i + 1
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

            entry_occ = ttk.Entry(parent_frame, width=8)
            entry_occ.grid(row=row, column=4, padx=2, pady=2)
            entry_occ.insert(0, str(atom["occ"]))
            widgets.append(entry_occ)

            entry_biso = ttk.Entry(parent_frame, width=8)
            entry_biso.grid(row=row, column=5, padx=2, pady=2)
            entry_biso.insert(0, str(atom["biso"]))
            widgets.append(entry_biso)

            self.atom_widgets.append(widgets)

    def add_atom(self):
        self.atoms.append(
            {"element": "C", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.0}
        )
        self.refresh_atoms_table(self.atoms_frame)

    def remove_atom(self):
        if len(self.atoms) > 1:
            self.atoms.pop()
            self.refresh_atoms_table(self.atoms_frame)
        else:
            messagebox.showwarning("Warning", "At least one atom required.")

    def collect_atoms_from_widgets(self):
        new_atoms = []
        for widgets in self.atom_widgets:
            try:
                element = widgets[0].get()
                x = _parse_float_locale(widgets[1].get())
                y = _parse_float_locale(widgets[2].get())
                z = _parse_float_locale(widgets[3].get())
                occ = _parse_float_locale(widgets[4].get())
                biso = _parse_float_locale(widgets[5].get())
                new_atoms.append(
                    {
                        "element": element,
                        "x": x,
                        "y": y,
                        "z": z,
                        "occ": occ,
                        "biso": biso,
                    }
                )
            except ValueError as e:
                messagebox.showerror("Input Error", f"Invalid number in atom: {e}")
                return None
        return new_atoms

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
                        "Input Error",
                        f"Invalid space group (Hall number or empty for auto): {sg_text!r}",
                    )
                    return

            bravais = self.bravais_centering_var.get().strip().lower()

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
                        "Ортогональная ячейка",
                        "Развёртка P/I/F/C/A/B задаётся в дробях по базису при α≈β≈γ≈90° "
                        "(куб, тетрагон, орторомб и т.п.). Атомы не разворачиваются.",
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

            try:
                intensity_min = _parse_float_locale(self.intensity_min_var.get())
            except ValueError:
                messagebox.showerror(
                    "Input Error",
                    f"Invalid intensity cutoff (min): {self.intensity_min_var.get()!r}",
                )
                return

            wl = _safe_double_get(self.wavelength_var, "wavelength")
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

            pattern = PowderPattern(
                self.name_var.get(),
                crystal,
                wl,
                tth_range,
                thetam_deg=thetam,
                U=U,
                V=V,
                W=W,
                scale=scale,
                profile=self.profile_var.get(),
                eta=eta,
                intensity_units=self.intensity_units_var.get(),
                normalize_intensity=self.normalize_intensity_var.get(),
                intensity_max_value=imax,
                intensity_min=intensity_min,
                multiplicity_mode=self.multiplicity_mode_var.get(),
                multiplicity_metric_rtol=mm_rtol,
                multiplicity_metric_atol=mm_atol,
            )

            run_dir = f"runs/{pattern.name}/"
            Plot(pattern).plot_curve(path=run_dir)
            plt.close("all")

            x, y = pattern.get_pattern_data()
            self.ax.clear()
            self.ax.plot(x, y)
            self.ax.set_xlabel("2θ (deg)")
            self.ax.set_ylabel("Intensity")
            y_top = float(np.max(y)) if len(y) else 1.0
            y_off = max(y_top * 0.015, 1e-9)
            for hkl, xc, y_peak in pattern.hkl_labels:
                h, k, l = (int(round(hkl[0])), int(round(hkl[1])), int(round(hkl[2])))
                label = f"{h}{k}{l}"
                self.ax.text(
                    xc,
                    y_peak + y_off,
                    label,
                    fontsize=6,
                    ha="center",
                    va="bottom",
                )
            self.figure.tight_layout(pad=1.2)
            self.canvas.draw()
            messagebox.showinfo(
                "Success",
                f"Saved under runs/{pattern.name}/: "
                f"{pattern.name}.tsv, G.csv, Gstar.csv, {pattern.name}_powder.png, {pattern.name}.png",
            )
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate pattern:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PowderPatternGUI(root)
    root.mainloop()
