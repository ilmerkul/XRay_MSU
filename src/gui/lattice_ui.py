"""Фрагмент GUI: LatticeUIMixin."""

import tkinter as tk

from .ui_text import ascii_ui_text


class LatticeUIMixin:
    @staticmethod
    def _is_orthogonal_cell_approx_from_values(al, be, ga, atol_deg=0.5) -> bool:
        """Проверяет, что углы ячейки близки к 90° (ортогональная база).

        Args:
            al: Угол α (градусы).
            be: Угол β (градусы).
            ga: Угол γ (градусы).
            atol_deg: Допуск от 90° (градусы).

        Returns:
            ``True``, если α≈β≈γ≈90° в пределах допуска.
        """
        return (
            abs(al - 90.0) < atol_deg
            and abs(be - 90.0) < atol_deg
            and abs(ga - 90.0) < atol_deg
        )

    def _lattice_family_key(self) -> str:
        """Возвращает внутренний ключ текущей сингонии из комбобокса.

        Returns:
            Ключ из ``LATTICE_FAMILY_KEYS`` или ``manual``.
        """
        cur = self.lattice_family_var.get().strip()
        for k in self.LATTICE_FAMILY_KEYS:
            if self._lattice_label(k) == cur:
                return k
            for labels in self.LATTICE_FAMILY_LABELS_BY_LANG.values():
                if ascii_ui_text(labels.get(k, "")) == cur:
                    return k
        return "manual"

    def _clear_lattice_traces(self):
        """Снимает все trace-обработчики синхронизации параметров ячейки."""
        for var, tid in self._lattice_trace_ids:
            try:
                var.trace_remove("write", tid)
            except (tk.TclError, ValueError):
                pass
        self._lattice_trace_ids.clear()

    def _trace_write(self, var, callback):
        """Подписывает переменную на изменение для синхронизации ячейки.

        Args:
            var: ``tk.Variable`` (обычно ``DoubleVar``).
            callback: Функция без аргументов, вызываемая при ``write``.
        """

        def _cb(*_):
            """Обёртка trace-callback без аргументов."""
            callback()

        tid = var.trace_add("write", _cb)
        self._lattice_trace_ids.append((var, tid))

    def _lock_cell_angle(self, which: str, value: float):
        """Фиксирует угол ячейки и блокирует поле ввода.

        Args:
            which: ``alpha``, ``beta`` или ``gamma``.
            value: Значение угла (градусы).
        """
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
        """Синхронизирует b и c с a для кубической/ромбоэдрической ячейки."""
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
        """Синхронизирует b с a для тетрагональной/гексагональной ячейки."""
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
        """Синхронизирует β и γ с α для ромбоэдрической ячейки."""
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
        """Обработчик смены сингонии в комбобоксе.

        Args:
            event: Событие комбобокса (не используется).
        """
        self._apply_lattice_constraints()

    def _apply_lattice_constraints(self, event=None):
        """Применяет ограничения параметров ячейки для выбранной сингонии.

        Args:
            event: Не используется (для совместимости с trace).
        """
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
