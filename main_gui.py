import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from src.model.atom.atom import Atom
from src.model.crystal.crystal import Crystal
from src.model.pattern.powder import PowderPattern


class PowderPatternGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Powder Pattern Generator")
        self.root.geometry("1000x800")

        self.name_var = tk.StringVar(value="NaCl")
        
        self.a_var = tk.DoubleVar(value=5.64)
        self.b_var = tk.DoubleVar(value=5.64)
        self.c_var = tk.DoubleVar(value=5.64)
        self.alpha_var = tk.DoubleVar(value=90.0)
        self.beta_var = tk.DoubleVar(value=90.0)
        self.gamma_var = tk.DoubleVar(value=90.0)
        self.space_group_var = tk.IntVar(value=523)

        self.atoms = [
            {"element": "Na", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.6},
            {"element": "Cl", "x": 0.5, "y": 0.5, "z": 0.5, "occ": 1.0, "biso": 1.35}
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

        self.create_widgets()

        self.figure = Figure(figsize=(6, 4), dpi=100)
        self.ax = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root)
        main_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        crystal_frame = ttk.LabelFrame(scrollable_frame, text="Crystal Parameters", padding=10)
        crystal_frame.pack(fill="x", padx=10, pady=5)

        row = 0
        ttk.Label(crystal_frame, text="Name:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.name_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="a (Å):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.a_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="b (Å):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.b_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="c (Å):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.c_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="α (°):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.alpha_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="β (°):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.beta_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="γ (°):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.gamma_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(crystal_frame, text="Space Group:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(crystal_frame, textvariable=self.space_group_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        atoms_frame = ttk.LabelFrame(scrollable_frame, text="Atoms", padding=10)
        atoms_frame.pack(fill="x", padx=10, pady=5)

        headers = ["Element", "x", "y", "z", "Occupancy", "Biso"]
        for col, h in enumerate(headers):
            ttk.Label(atoms_frame, text=h, font=('Arial', 10, 'bold')).grid(row=0, column=col, padx=2, pady=2)

        self.atom_widgets = []
        self.refresh_atoms_table(atoms_frame)

        btn_frame = ttk.Frame(atoms_frame)
        btn_frame.grid(row=100, column=0, columnspan=6, pady=5)
        ttk.Button(btn_frame, text="Add Atom", command=self.add_atom).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Remove Last Atom", command=self.remove_atom).pack(side=tk.LEFT, padx=5)

        pattern_frame = ttk.LabelFrame(scrollable_frame, text="Pattern Parameters", padding=10)
        pattern_frame.pack(fill="x", padx=10, pady=5)

        row = 0
        ttk.Label(pattern_frame, text="Wavelength (Å):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.wavelength_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="2θ range (start, end, step):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        range_frame = ttk.Frame(pattern_frame)
        range_frame.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        ttk.Entry(range_frame, textvariable=self.tth_start_var, width=8).pack(side=tk.LEFT)
        ttk.Label(range_frame, text="—").pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.tth_end_var, width=8).pack(side=tk.LEFT)
        ttk.Label(range_frame, text="step").pack(side=tk.LEFT)
        ttk.Entry(range_frame, textvariable=self.tth_step_var, width=8).pack(side=tk.LEFT)
        row += 1

        ttk.Label(pattern_frame, text="U:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.U_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="V:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.V_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="W:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.W_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Scale:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.scale_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Profile:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        profile_combo = ttk.Combobox(pattern_frame, textvariable=self.profile_var,
                                     values=["stick", "gaussian", "lorentzian", "pseudo-voigt"])
        profile_combo.grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Eta (for pseudo-voigt):").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.eta_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Intensity units:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.intensity_units_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Normalize intensity:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Checkbutton(pattern_frame, variable=self.normalize_intensity_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Label(pattern_frame, text="Max intensity value:").grid(row=row, column=0, sticky="e", padx=5, pady=2)
        ttk.Entry(pattern_frame, textvariable=self.intensity_max_value_var).grid(row=row, column=1, sticky="w", padx=5, pady=2)
        row += 1

        ttk.Button(scrollable_frame, text="Generate Pattern", command=self.generate_pattern).pack(pady=10)

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
            # x
            entry_x = ttk.Entry(parent_frame, width=8)
            entry_x.grid(row=row, column=1, padx=2, pady=2)
            entry_x.insert(0, str(atom["x"]))
            widgets.append(entry_x)
            # y
            entry_y = ttk.Entry(parent_frame, width=8)
            entry_y.grid(row=row, column=2, padx=2, pady=2)
            entry_y.insert(0, str(atom["y"]))
            widgets.append(entry_y)
            # z
            entry_z = ttk.Entry(parent_frame, width=8)
            entry_z.grid(row=row, column=3, padx=2, pady=2)
            entry_z.insert(0, str(atom["z"]))
            widgets.append(entry_z)
            # occ
            entry_occ = ttk.Entry(parent_frame, width=8)
            entry_occ.grid(row=row, column=4, padx=2, pady=2)
            entry_occ.insert(0, str(atom["occ"]))
            widgets.append(entry_occ)
            # biso
            entry_biso = ttk.Entry(parent_frame, width=8)
            entry_biso.grid(row=row, column=5, padx=2, pady=2)
            entry_biso.insert(0, str(atom["biso"]))
            widgets.append(entry_biso)

            self.atom_widgets.append(widgets)

    def add_atom(self):
        self.atoms.append({"element": "C", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.0})
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.LabelFrame) and sub["text"] == "Atoms":
                        self.refresh_atoms_table(sub)
                        return

    def remove_atom(self):
        if len(self.atoms) > 1:
            self.atoms.pop()
            for child in self.root.winfo_children():
                if isinstance(child, ttk.Frame):
                    for sub in child.winfo_children():
                        if isinstance(sub, ttk.LabelFrame) and sub["text"] == "Atoms":
                            self.refresh_atoms_table(sub)
                            return
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
                new_atoms.append({"element": element, "x": x, "y": y, "z": z, "occ": occ, "biso": biso})
            except ValueError as e:
                messagebox.showerror("Input Error", f"Invalid number in atom: {e}")
                return None
        return new_atoms

    def generate_pattern(self):
        try:
            atoms_data = self.collect_atoms_from_widgets()
            if atoms_data is None:
                return

            atom_objects = [Atom(atom["element"], atom["x"], atom["y"], atom["z"], atom["occ"], atom["biso"])
                            for atom in atoms_data]

            crystal = Crystal(
                self.a_var.get(),
                self.b_var.get(),
                self.c_var.get(),
                self.alpha_var.get(),
                self.beta_var.get(),
                self.gamma_var.get(),
                self.space_group_var.get(),
                atom_objects
            )

            tth_range = [self.tth_start_var.get(), self.tth_end_var.get(), self.tth_step_var.get()]

            pattern = PowderPattern(
                self.name_var.get(),
                crystal,
                self.wavelength_var.get(),
                tth_range,
                U=self.U_var.get(),
                V=self.V_var.get(),
                W=self.W_var.get(),
                scale=self.scale_var.get(),
                profile=self.profile_var.get(),
                eta=self.eta_var.get(),
                intensity_units=self.intensity_units_var.get(),
                normalize_intensity=self.normalize_intensity_var.get(),
                intensity_max_value=self.intensity_max_value_var.get(),
            )

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