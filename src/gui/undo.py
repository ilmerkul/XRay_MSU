"""Отмена последнего изменения параметров формы."""

from __future__ import annotations

import copy
import tkinter as tk


class UndoMixin:
    """Миксин: стек снимков состояния формы и Edit → Undo."""

    _UNDO_STACK_LIMIT = 50

    _PLOT_GUI_VAR_NAMES = (
        "plot_line_width_var",
        "plot_antialiased_var",
        "plot_grid_major_var",
        "plot_grid_minor_var",
        "plot_grid_major_alpha_var",
        "plot_grid_minor_alpha_var",
        "plot_grid_major_lw_var",
        "plot_grid_minor_lw_var",
        "plot_vlines_var",
        "plot_vline_width_var",
        "plot_vline_alpha_var",
        "plot_title_show_var",
        "plot_legend_show_var",
        "plot_legend_loc_var",
        "plot_tick_label_size_var",
        "plot_axis_label_size_var",
        "plot_title_size_var",
        "plot_peak_label_size_var",
        "plot_y_top_margin_var",
        "plot_layout_pad_var",
        "plot_dpi_var",
        "plot_aspect_var",
        "label_angles_var",
        "label_angles_hkl_var",
    )

    def _init_undo(self) -> None:
        self._undo_stack: list[dict] = []
        self._undo_restoring = False
        self._undo_menu = None
        self._last_form_snapshot: dict | None = None
        self._form_focus_undo = False

    def _capture_plot_gui_state(self) -> dict:
        state: dict = {}
        for name in self._PLOT_GUI_VAR_NAMES:
            var = getattr(self, name, None)
            if var is None:
                continue
            try:
                state[name] = var.get()
            except tk.TclError:
                pass
        state["_plot_aspect"] = getattr(self, "_plot_aspect", 1.25)
        return state

    def _restore_plot_gui_state(self, state: dict) -> None:
        for name in self._PLOT_GUI_VAR_NAMES:
            if name not in state:
                continue
            var = getattr(self, name, None)
            if var is None:
                continue
            try:
                var.set(state[name])
            except tk.TclError:
                pass
        aspect = state.get("_plot_aspect")
        if aspect is not None:
            try:
                self._plot_aspect = float(aspect)
                self.plot_aspect_var.set(float(aspect))
            except (tk.TclError, ValueError, AttributeError):
                pass

    def _capture_form_snapshot(self) -> dict:
        """Снимок текущих параметров формы для восстановления."""
        snap = copy.deepcopy(self.collect_run_config())
        snap["_gui_show_biso"] = bool(self.show_biso_var.get())
        if hasattr(self, "config_combo"):
            snap["_gui_config_combo"] = self.config_combo.get().strip()
        else:
            snap["_gui_config_combo"] = ""
        snap["_gui_calc_results"] = copy.deepcopy(getattr(self, "_calc_results", []))
        snap["_gui_selected_calc_indices"] = list(
            getattr(self, "_selected_calc_indices", [])
        )
        snap["_gui_plot"] = self._capture_plot_gui_state()
        return snap

    def _push_undo_snapshot(self) -> None:
        """Сохраняет последнее зафиксированное состояние перед изменением."""
        if self._undo_restoring:
            return
        if self._last_form_snapshot is not None:
            self._undo_stack.append(copy.deepcopy(self._last_form_snapshot))
            if len(self._undo_stack) > self._UNDO_STACK_LIMIT:
                self._undo_stack.pop(0)
        self._update_undo_menu_state()

    def _commit_form_state(self) -> None:
        """Фиксирует текущее состояние формы как базовое для следующей отмены."""
        if self._undo_restoring:
            return
        self._last_form_snapshot = self._capture_form_snapshot()

    def _register_form_undo_widget(self, widget) -> None:
        """Одна отмена на сессию редактирования поля (FocusIn → FocusOut)."""
        if getattr(widget, "_xray_undo_registered", False):
            return
        widget._xray_undo_registered = True

        def on_focus_in(_event=None):
            if self._undo_restoring:
                return
            if not self._form_focus_undo:
                self._push_undo_snapshot()
                self._form_focus_undo = True

        def on_focus_out(_event=None):
            if self._form_focus_undo and not self._undo_restoring:
                self._form_focus_undo = False
                self._commit_form_state()

        widget.bind("<FocusIn>", on_focus_in, add="+")
        widget.bind("<FocusOut>", on_focus_out, add="+")

    def _register_form_undo_combobox(self, combo, callback) -> None:
        """Отмена при смене значения в readonly combobox."""

        def on_selected(event=None):
            if not self._undo_restoring:
                self._push_undo_snapshot()
            try:
                callback(event)
            finally:
                if not self._undo_restoring:
                    self._commit_form_state()

        combo.bind("<<ComboboxSelected>>", on_selected, add="+")

    def _restore_form_snapshot(self, snap: dict) -> None:
        """Восстанавливает форму из снимка."""
        snap = copy.deepcopy(snap)
        show_biso = bool(snap.pop("_gui_show_biso", False))
        config_sel = str(snap.pop("_gui_config_combo", ""))
        calc_results = snap.pop("_gui_calc_results", None)
        selected_indices = snap.pop("_gui_selected_calc_indices", [])
        plot_state = snap.pop("_gui_plot", None)
        prev_biso = bool(self.show_biso_var.get())

        self._undo_restoring = True
        try:
            if plot_state is not None:
                self._restore_plot_gui_state(plot_state)
            self.show_biso_var.set(show_biso)
            self.apply_config(snap)
            if show_biso != prev_biso and getattr(self, "atoms_frame", None):
                self._build_atom_headers(self.atoms_frame)
                self.refresh_atoms_table(self.atoms_frame)
            if hasattr(self, "config_combo"):
                if config_sel and config_sel in self.config_files:
                    self.config_combo.set(config_sel)
                else:
                    self.config_combo.set("")
            if calc_results is not None:
                self._calc_results = calc_results
                self._refresh_calc_results_list()
                valid = [i for i in selected_indices if 0 <= i < len(calc_results)]
                if valid:
                    self._select_calc_result_indices(valid)
                else:
                    self._selected_calc_indices = []
                    if calc_results:
                        self._select_calc_result_index(0)
                    elif hasattr(self, "ax"):
                        self._clear_calc_plot()
            if hasattr(self, "_on_profile_selected"):
                self._on_profile_selected()
        finally:
            self._undo_restoring = False
        self._last_form_snapshot = copy.deepcopy(self._capture_form_snapshot())

    def _undo_last_action(self, _event=None) -> None:
        """Отменяет последнее изменение параметров формы."""
        if not self._undo_stack:
            return
        snap = self._undo_stack.pop()
        self._restore_form_snapshot(snap)
        self._update_undo_menu_state()
        return "break" if _event is not None else None

    def _update_undo_menu_state(self) -> None:
        menu = getattr(self, "_undo_menu", None)
        if menu is None:
            return
        state = tk.NORMAL if self._undo_stack else tk.DISABLED
        try:
            menu.entryconfig(0, state=state)
        except tk.TclError:
            pass
