"""Фрагмент GUI: CalculationMixin."""

from __future__ import annotations

import threading
from tkinter import messagebox

import numpy as np

from ..model.atom.atom import Atom
from ..model.crystal.crystal import Crystal
from ..model.crystal.utils import expand_atoms_bravais_centering
from ..model.pattern.powder import PowderPattern
from ..model.pattern.utils import normalize_profile
from .helpers import parse_float_locale, safe_double_get
from .progress_dialog import ProgressDialog
from .ui_text import ascii_ui_text


class CalculationMixin:
    def generate_pattern(self):
        """Считывает параметры формы и запускает расчёт с окном прогресса."""
        if getattr(self, "_calc_running", False):
            return
        params = self._prepare_calculation_inputs()
        if params is None:
            return

        self._calc_running = True
        dialog = ProgressDialog(
            self.root,
            self.tr("calc_progress_title"),
            self.tr("calc_progress_start"),
            self._current_theme(),
            self.fonts,
        )
        dialog.set_progress(0.02, self.tr("calc_progress_start"))

        thread = threading.Thread(
            target=self._run_calculation_worker,
            args=(params, dialog),
            daemon=True,
        )
        thread.start()

    def _report_calc_progress(
        self,
        dialog: ProgressDialog,
        fraction: float,
        message_key: str,
        **fmt,
    ) -> None:
        """Обновляет прогресс в главном потоке (``tr`` нельзя вызывать из worker)."""

        def update() -> None:
            message = (
                self.tr(message_key).format(**fmt) if fmt else self.tr(message_key)
            )
            dialog.set_progress(fraction, message)

        self.root.after(0, update)

    def _prepare_calculation_inputs(self) -> dict | None:
        """Проверяет форму и собирает параметры расчёта."""
        atoms_data = self.collect_atoms_from_widgets()
        if atoms_data is None:
            return None

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
                return None

        bravais = self.bravais_centering_var.get().strip().lower()
        if bravais in ("", "none", "p"):
            bravais = "none"

        a = safe_double_get(self.a_var, ascii_ui_text("a (Å)"))
        b = safe_double_get(self.b_var, ascii_ui_text("b (Å)"))
        c = safe_double_get(self.c_var, ascii_ui_text("c (Å)"))
        alpha = safe_double_get(self.alpha_var, ascii_ui_text("α (deg)"))
        beta = safe_double_get(self.beta_var, ascii_ui_text("β (deg)"))
        gamma = safe_double_get(self.gamma_var, ascii_ui_text("γ (deg)"))
        if None in (a, b, c, alpha, beta, gamma):
            return None

        expand_bravais = False
        if spacegroup_number is None and bravais not in ("", "none"):
            if not self._is_orthogonal_cell_approx_from_values(alpha, beta, gamma):
                messagebox.showwarning(
                    self.tr("orthogonal_cell_title"),
                    self.tr("orthogonal_cell_warning"),
                )
            else:
                expand_bravais = True

        tth_s = safe_double_get(self.tth_start_var, ascii_ui_text("2θ start"))
        tth_e = safe_double_get(self.tth_end_var, ascii_ui_text("2θ end"))
        tth_step = safe_double_get(self.tth_step_var, ascii_ui_text("2θ step"))
        if None in (tth_s, tth_e, tth_step):
            return None

        wl = safe_double_get(self.wavelength_var, "wavelength")
        wl2_text = (
            self.wavelength2_var.get().strip()
            if self.wavelength2_enabled_var.get()
            else ""
        )
        wl2 = None
        if wl2_text:
            try:
                wl2 = parse_float_locale(wl2_text)
                if wl2 <= 0:
                    raise ValueError
            except ValueError:
                messagebox.showerror(
                    self.tr("input_error_title"),
                    self.tr("invalid_second_wavelength").format(value=wl2_text),
                )
                return None

        thetam = safe_double_get(self.thetam_deg_var, ascii_ui_text("θ_m"))
        U = safe_double_get(self.U_var, "U")
        V = safe_double_get(self.V_var, "V")
        W = safe_double_get(self.W_var, "W")
        scale = safe_double_get(self.scale_var, "scale")
        eta = safe_double_get(self.eta_var, ascii_ui_text("η"))
        imax = safe_double_get(self.intensity_max_value_var, "intensity max")
        mm_rtol = safe_double_get(
            self.multiplicity_metric_rtol_var, "multiplicity rtol"
        )
        mm_atol = safe_double_get(
            self.multiplicity_metric_atol_var, "multiplicity atol"
        )
        if None in (wl, thetam, U, V, W, scale, eta, imax, mm_rtol, mm_atol):
            return None

        wavelengths = [wl]
        wl2_ratio = 1.0
        if wl2 is not None:
            wavelengths.append(wl2)
            wl2_ratio = safe_double_get(
                self.wl2_intensity_ratio_var, ascii_ui_text("I(λ2)/I(λ1)")
            )
            if wl2_ratio is None:
                return None
            if wl2_ratio < 0:
                messagebox.showerror(
                    self.tr("input_error_title"),
                    self.tr("invalid_ratio_nonnegative"),
                )
                return None

        return {
            "atom_objects": atom_objects,
            "spacegroup_number": spacegroup_number,
            "bravais": bravais,
            "expand_bravais": expand_bravais,
            "a": a,
            "b": b,
            "c": c,
            "alpha": alpha,
            "beta": beta,
            "gamma": gamma,
            "tth_range": np.array([tth_s, tth_e, tth_step]),
            "wavelengths": wavelengths,
            "wl2": wl2,
            "wl2_ratio": wl2_ratio,
            "thetam": thetam,
            "U": U,
            "V": V,
            "W": W,
            "scale": scale,
            "eta": eta,
            "imax": imax,
            "mm_rtol": mm_rtol,
            "mm_atol": mm_atol,
            "base_name": self.name_var.get().strip() or "pattern",
            "profile": self._profile_key(),
            "intensity_units": self.intensity_units_var.get(),
            "normalize_intensity": self.normalize_intensity_var.get(),
        }

    @staticmethod
    def _atoms_cache_tuple(atom_objects) -> tuple:
        return tuple(
            (
                atom.element,
                round(float(atom.frac[0]), 8),
                round(float(atom.frac[1]), 8),
                round(float(atom.frac[2]), 8),
                round(float(atom.occ), 8),
                round(float(atom.Biso), 8),
            )
            for atom in atom_objects
        )

    def _reflection_cache_key(self, params: dict, atom_objects) -> tuple:
        """Ключ кэша отражений (всё, кроме профиля и сетки 2θ)."""
        return (
            round(params["a"], 8),
            round(params["b"], 8),
            round(params["c"], 8),
            round(params["alpha"], 8),
            round(params["beta"], 8),
            round(params["gamma"], 8),
            params["spacegroup_number"],
            self._atoms_cache_tuple(atom_objects),
            tuple(round(float(w), 8) for w in params["wavelengths"]),
            round(params["thetam"], 8),
            round(params["U"], 12),
            round(params["V"], 12),
            round(params["W"], 12),
            round(params["scale"], 8),
            bool(params["normalize_intensity"]),
            round(params["imax"], 8),
            round(params["mm_rtol"], 12),
            round(params["mm_atol"], 12),
            bool(self.structure_factor_local),
            str(params["intensity_units"]),
        )

    def _make_powder_pattern(
        self,
        *,
        name: str,
        crystal: Crystal,
        wavelength: float,
        params: dict,
        reflections=None,
    ) -> PowderPattern:
        return PowderPattern(
            name,
            crystal,
            wavelength,
            params["tth_range"],
            thetam_deg=params["thetam"],
            U=params["U"],
            V=params["V"],
            W=params["W"],
            scale=params["scale"],
            profile=normalize_profile(params["profile"]),
            eta=params["eta"],
            intensity_units=params["intensity_units"],
            normalize_intensity=params["normalize_intensity"],
            intensity_max_value=params["imax"],
            intensity_min=1e-6,
            multiplicity_mode="metric",
            multiplicity_metric_rtol=params["mm_rtol"],
            multiplicity_metric_atol=params["mm_atol"],
            local=self.structure_factor_local,
            reflections=reflections,
        )

    def _run_calculation_worker(self, params: dict, dialog: ProgressDialog) -> None:
        try:
            atom_objects = list(params["atom_objects"])
            if params["expand_bravais"]:
                atom_objects = expand_atoms_bravais_centering(
                    atom_objects, params["bravais"].upper()
                )

            cache_key = self._reflection_cache_key(params, atom_objects)
            cache = getattr(self, "_reflection_cache", None) or {}
            reuse_reflections = (
                cache.get("key") == cache_key
                and cache.get("crystal") is not None
                and cache.get("reflections_by_wl")
            )

            if reuse_reflections:
                self._report_calc_progress(dialog, 0.12, "calc_progress_reuse")
                crystal = cache["crystal"]
            else:
                self._report_calc_progress(dialog, 0.08, "calc_progress_crystal")
                crystal = Crystal(
                    params["a"],
                    params["b"],
                    params["c"],
                    params["alpha"],
                    params["beta"],
                    params["gamma"],
                    asf=self.asf,
                    spacegroup_number=params["spacegroup_number"],
                    atoms=atom_objects,
                )
                cache = {
                    "key": cache_key,
                    "crystal": crystal,
                    "reflections_by_wl": {},
                }

            patterns = []
            wavelengths = params["wavelengths"]
            n_wl = len(wavelengths)
            for idx, wli in enumerate(wavelengths, start=1):
                suffix = "" if idx == 1 else f"_wl{idx}"
                cached_refl = cache["reflections_by_wl"].get(wli)
                if reuse_reflections and cached_refl is not None:
                    self._report_calc_progress(
                        dialog,
                        0.12 + 0.58 * (idx / n_wl),
                        "calc_progress_curve",
                        n=idx,
                        total=n_wl,
                    )
                    pattern_i = self._make_powder_pattern(
                        name=f"{params['base_name']}{suffix}",
                        crystal=crystal,
                        wavelength=wli,
                        params=params,
                        reflections=cached_refl,
                    )
                else:
                    wl_frac = (idx - 1) / n_wl
                    self._report_calc_progress(
                        dialog,
                        0.12 + 0.58 * wl_frac,
                        "calc_progress_pattern",
                        n=idx,
                        total=n_wl,
                    )
                    pattern_i = self._make_powder_pattern(
                        name=f"{params['base_name']}{suffix}",
                        crystal=crystal,
                        wavelength=wli,
                        params=params,
                    )
                    cache["reflections_by_wl"][wli] = pattern_i.reflections
                    self._report_calc_progress(
                        dialog,
                        0.12 + 0.58 * (idx / n_wl),
                        "calc_progress_curve",
                        n=idx,
                        total=n_wl,
                    )
                patterns.append(pattern_i)

            self._reflection_cache = cache

            self._report_calc_progress(dialog, 0.78, "calc_progress_combine")
            x, y = patterns[0].get_pattern_data()
            y_combined = np.array(y, copy=True)
            all_reflections = list(patterns[0].reflections)
            wl2_ratio = params["wl2_ratio"]
            for p in patterns[1:]:
                xp, yp = p.get_pattern_data()
                yp_scaled = wl2_ratio * np.asarray(yp, dtype=float)
                if len(xp) == len(x) and np.allclose(xp, x):
                    y_combined += yp_scaled
                else:
                    y_combined += np.interp(x, xp, yp_scaled)
                all_reflections.extend(p.reflections)

            result_payload = {
                "base_name": params["base_name"],
                "patterns": patterns,
                "wl2_ratio": wl2_ratio,
                "x": x,
                "y_combined": y_combined,
                "all_reflections": all_reflections,
                "wavelengths": wavelengths,
                "normalize_intensity": params["normalize_intensity"],
                "wl2": params["wl2"],
            }
            self._report_calc_progress(dialog, 0.92, "calc_progress_done")
            self.root.after(
                0,
                lambda payload=result_payload: self._finish_calculation(
                    payload, dialog
                ),
            )
        except Exception as exc:
            self.root.after(
                0,
                lambda error=exc: self._fail_calculation(error, dialog),
            )

    def _finish_calculation(self, payload: dict, dialog: ProgressDialog) -> None:
        try:
            dialog.set_progress(1.0, self.tr("calc_progress_done"))
            self._append_calc_result(
                payload["base_name"],
                payload["patterns"],
                payload["wl2_ratio"],
                payload["x"],
                payload["y_combined"],
                payload["all_reflections"],
                payload["wavelengths"],
                normalize_intensity=payload["normalize_intensity"],
            )
            wl_msg = ", ".join(f"{w:.4f} A" for w in payload["wavelengths"])
            ratio_msg = (
                self.tr("ratio_on_plot").format(ratio=payload["wl2_ratio"])
                if payload["wl2"] is not None
                else ""
            )
            messagebox.showinfo(
                self.tr("success_title"),
                self.tr("calc_done_message").format(
                    wl_msg=wl_msg,
                    ratio_msg=ratio_msg,
                ),
            )
        except Exception as exc:
            self._fail_calculation(exc, dialog)
        finally:
            dialog.close()
            self._calc_running = False

    def _fail_calculation(self, error: Exception, dialog: ProgressDialog) -> None:
        dialog.close()
        self._calc_running = False
        messagebox.showerror(
            self.tr("error_title"),
            self.tr("failed_generate_pattern").format(error=str(error)),
        )
