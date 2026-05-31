"""Тесты UndoMixin."""

from __future__ import annotations

import copy
from unittest.mock import MagicMock

from src.gui.undo import UndoMixin


class _UndoHost(UndoMixin):
    def __init__(self):
        self._init_undo()
        self._undo_restoring = False
        self._calc_results = []
        self._selected_calc_indices = []
        self.show_biso_var = MagicMock()
        self.show_biso_var.get.return_value = False
        self.config_combo = MagicMock()
        self.config_combo.get.return_value = "Cu"
        self.config_files = {"Cu": "/tmp/Cu.yaml"}
        self.atoms_frame = None
        self._capture_plot_gui_state = MagicMock(return_value={})
        self._restore_plot_gui_state = MagicMock()
        self._refresh_calc_results_list = MagicMock()
        self._select_calc_result_indices = MagicMock()
        self._select_calc_result_index = MagicMock()
        self._clear_calc_plot = MagicMock()
        self._commit_form_state()

    def collect_run_config(self):
        return {"name": "NaCl", "a": 5.64, "atoms": [["Na", 0, 0, 0, 1, 1.6]]}

    def apply_config(self, config):
        if not self._undo_restoring:
            self._push_undo_snapshot()
        self.last_applied = copy.deepcopy(config)
        if not self._undo_restoring:
            self._commit_form_state()

    def _build_atom_headers(self, _frame):
        pass

    def refresh_atoms_table(self, _frame):
        pass

    def _on_profile_selected(self, _event=None):
        pass


def test_push_undo_and_restore():
    host = _UndoHost()
    host.apply_config({"name": "Cu", "a": 3.6})
    assert host.last_applied["name"] == "Cu"
    assert len(host._undo_stack) == 1

    host._undo_last_action()
    assert host.last_applied["name"] == "NaCl"
    assert host._undo_stack == []


def test_restore_does_not_push_undo():
    host = _UndoHost()
    host.apply_config({"name": "Cu", "a": 3.6})
    host._undo_last_action()
    assert len(host._undo_stack) == 0
