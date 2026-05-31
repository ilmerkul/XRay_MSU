"""Фрагмент GUI: AtomsMixin."""

import tkinter as tk
from tkinter import messagebox, ttk

from ..model.atom.atom import AtomicScatteringFactor
from .helpers import parse_float_locale


class AtomsMixin:
    def _build_atom_headers(self, parent_frame):
        """Перестраивает заголовки таблицы атомов (с опциональной колонкой B_iso).

        Args:
            parent_frame: Фрейм секции атомов.
        """
        for w in self._atom_header_labels:
            w.destroy()
        self._atom_header_labels.clear()
        headers = [self.tr("element_col"), "x", "y", "z"]
        if self.show_biso_var.get():
            headers.append("Biso")
        for col, h in enumerate(headers):
            lab = ttk.Label(parent_frame, text=h, style="InsetHead.TLabel")
            lab.grid(row=1, column=col, padx=2, pady=2)
            self._atom_header_labels.append(lab)

    def _on_toggle_biso_column(self):
        """Переключает видимость колонки B_iso и обновляет таблицу атомов."""
        self._push_undo_snapshot()
        synced = self.collect_atoms_from_widgets()
        if synced is not None:
            self.atoms = synced
        self._build_atom_headers(self.atoms_frame)
        self.refresh_atoms_table(self.atoms_frame)
        self._commit_form_state()

    def refresh_atoms_table(self, parent_frame):
        """Перерисовывает строки таблицы атомов из ``self.atoms``.

        Args:
            parent_frame: Фрейм секции атомов.
        """
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

        if hasattr(self, "_register_form_undo_widgets"):
            self._register_form_undo_widgets()

    def add_atom(self):
        """Добавляет новую строку атома (углерод по умолчанию) в таблицу."""
        atoms_data = self.collect_atoms_from_widgets()
        if atoms_data is None:
            return
        self._push_undo_snapshot()
        self.atoms = atoms_data
        self.atoms.append(
            {"element": "C", "x": 0.0, "y": 0.0, "z": 0.0, "occ": 1.0, "biso": 1.0}
        )
        self.refresh_atoms_table(self.atoms_frame)
        self._commit_form_state()

    def remove_atom(self):
        """Удаляет последний атом из таблицы (минимум один атом обязателен)."""
        if len(self.atoms) <= 1:
            messagebox.showwarning(
                self.tr("warning_title"), self.tr("at_least_one_atom")
            )
            return
        atoms_data = self.collect_atoms_from_widgets()
        if atoms_data is None:
            return
        self._push_undo_snapshot()
        self.atoms = atoms_data
        self.atoms.pop()
        self.refresh_atoms_table(self.atoms_frame)
        self._commit_form_state()

    def collect_atoms_from_widgets(self):
        """Считывает атомы из полей ввода таблицы.

        Returns:
            Список словарей атомов или ``None`` при ошибке ввода.
        """
        new_atoms = []
        for i, widgets in enumerate(self.atom_widgets):
            try:
                element = widgets[0].get()
                x = parse_float_locale(widgets[1].get())
                y = parse_float_locale(widgets[2].get())
                z = parse_float_locale(widgets[3].get())
                if widgets[4] is not None:
                    biso = parse_float_locale(widgets[4].get())
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
