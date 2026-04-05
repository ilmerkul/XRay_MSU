import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib

matplotlib.use("TkAgg")
import glob
import json
import os

import numpy as np

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

from src.model.atom.atom import Atom, AtomicScatteringFactor
from src.model.crystal.crystal import Crystal
from src.model.pattern.powder import PowderPattern


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
        self.space_group_var = tk.IntVar(value=225)

        self.atoms = [
            {"element": "Na", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.6},
            {"element": "Cl", "x": 0.5, "y": 0.5, "z": 0.5, "occ": 1.0, "biso": 1.35},
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
        self.intensity_min_var = tk.DoubleVar(value=1e-6)

        self.config_dir = self.find_config_dir()
        asf_path = self.find_asf_data_path()
        self.asf = AtomicScatteringFactor(asf_path)
        self.config_files = {}
        self.atoms_frame = None

        self.create_widgets()
        self.scan_config_files()

        fig_w = max(6.0, min(16.0, (sw - 80) / 100))
        self.figure = Figure(figsize=(fig_w, 4.5), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def find_config_dir(self):
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
        self.form_container = ttk.Frame(self.root)
        self.form_container.pack(side=tk.TOP, fill=tk.X)

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

        ttk.Label(crystal_frame, text="Space Group:").grid(
            row=row, column=0, sticky="e", padx=5, pady=2
        )
        ttk.Entry(crystal_frame, textvariable=self.space_group_var).grid(
            row=row, column=1, sticky="ew", padx=5, pady=2
        )
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

        ttk.Button(
            self.form_container, text="Generate Pattern", command=self.generate_pattern
        ).pack(pady=10)

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
            if not YAML_AVAILABLE:
                raise ImportError(
                    "PyYAML is not installed. Please install it to use YAML configs."
                )
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
        if "space_group" in config and config["space_group"] is not None:
            self.space_group_var.set(int(config["space_group"]))

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
        if "intensity_min" in config:
            self.intensity_min_var.set(float(config["intensity_min"]))

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
                x = float(widgets[1].get())
                y = float(widgets[2].get())
                z = float(widgets[3].get())
                occ = float(widgets[4].get())
                biso = float(widgets[5].get())
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

            crystal = Crystal(
                self.a_var.get(),
                self.b_var.get(),
                self.c_var.get(),
                self.alpha_var.get(),
                self.beta_var.get(),
                self.gamma_var.get(),
                asf=self.asf,
                spacegroup_number=self.space_group_var.get(),
                atoms=atom_objects,
            )

            tth_range = np.array(
                [
                    self.tth_start_var.get(),
                    self.tth_end_var.get(),
                    self.tth_step_var.get(),
                ]
            )

            pattern = PowderPattern(
                self.name_var.get(),
                crystal,
                self.wavelength_var.get(),
                tth_range,
                thetam_deg=self.thetam_deg_var.get(),
                U=self.U_var.get(),
                V=self.V_var.get(),
                W=self.W_var.get(),
                scale=self.scale_var.get(),
                profile=self.profile_var.get(),
                eta=self.eta_var.get(),
                intensity_units=self.intensity_units_var.get(),
                normalize_intensity=self.normalize_intensity_var.get(),
                intensity_max_value=self.intensity_max_value_var.get(),
                intensity_min=self.intensity_min_var.get(),
            )

            os.makedirs("images", exist_ok=True)
            crystal.save_image(f"images/{pattern.name}.png")

            x, y = pattern.get_pattern_data()
            self.ax.clear()
            self.ax.plot(x, y)
            self.ax.set_xlabel("2θ (deg)")
            self.ax.set_ylabel("Intensity")
            self.canvas.draw()
            messagebox.showinfo("Success", "Pattern generated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate pattern:\n{str(e)}")


if __name__ == "__main__":
    root = tk.Tk()
    app = PowderPatternGUI(root)
    root.mainloop()
