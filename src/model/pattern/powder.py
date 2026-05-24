import json
from pathlib import Path
from typing import Dict, Optional, Union

import numpy as np

from ..crystal.crystal import Crystal
from ..crystal.structure import atom_f_column_labels, structure_factor
from .utils import (
    CAGLIOTI_U_DEFAULT,
    CAGLIOTI_V_DEFAULT,
    CAGLIOTI_W_DEFAULT,
    NumpyEncoder,
    array_weight,
    caglioti_fwhm,
    gaussian,
    l_factor,
    lorentzian,
    normalize_profile,
    p_factor,
    pseudo_voigt,
)


def _format_F_tsv(F: complex, eps: float = 1e-9) -> str:
    """Строка для TSV: при F≈0 — «0», иначе компактно без -0.000j."""
    z = complex(F)
    if abs(z) < eps:
        return "0"
    r, i = z.real, z.imag
    if abs(i) < eps:
        return f"{r:.3f}"
    if abs(r) < eps:
        return f"{i:.3f}j"
    return f"{r:.3f}{i:+.3f}j"


class PowderPattern:
    def __init__(
        self,
        name: str,
        crystal: Crystal,
        wavelength: float,
        twotheta_range: np.ndarray,
        thetam_deg: float,
        U: float = CAGLIOTI_U_DEFAULT,
        V: float = CAGLIOTI_V_DEFAULT,
        W: float = CAGLIOTI_W_DEFAULT,
        scale: float = 1.0,
        profile: str = "pvoigt",
        eta: float = 0.5,
        bg_poly=None,
        intensity_units: str = "arbitrary",
        normalize_intensity: bool = True,
        intensity_max_value: float = 100.0,
        save_ref: bool = False,
        intensity_min: float = 1e-6,
        multiplicity_mode: str = "symmetry",
        multiplicity_metric_rtol: float = 1e-7,
        multiplicity_metric_atol: float = 1e-12,
    ):
        self.name = name
        self.crystal = crystal
        self.wavelength = wavelength
        self.twotheta = np.arange(
            twotheta_range[0], twotheta_range[1], twotheta_range[2]
        )
        self.thetam_deg = thetam_deg
        self.U, self.V, self.W = U, V, W
        self.scale = scale
        self.profile = normalize_profile(profile)
        self.eta = eta
        self.bg_poly = bg_poly if bg_poly is not None else [0, 0, 0]
        self.intensity_units = intensity_units
        self.normalize_intensity = normalize_intensity
        self.intensity_max_value = intensity_max_value
        self.save_ref = save_ref
        self.intensity_min = intensity_min
        _mm = (
            multiplicity_mode.lower()
            if isinstance(multiplicity_mode, str)
            else "symmetry"
        )
        if _mm not in ("symmetry", "metric"):
            raise ValueError(
                "multiplicity_mode must be 'symmetry' or 'metric', "
                f"got {multiplicity_mode!r}"
            )
        self.multiplicity_mode = _mm
        self.multiplicity_metric_rtol = multiplicity_metric_rtol
        self.multiplicity_metric_atol = multiplicity_metric_atol

        self.reflections = self._generate_reflections(d_min=self.wavelength / 2.0)
        self.ycalc, self.hkl_labels = self._convolve()

    def _generate_reflections(self, d_min):
        Gstar = self.crystal.Gstar
        eigvals = np.linalg.eigvalsh(Gstar)
        lambda_min_star = np.min(eigvals)

        assert lambda_min_star > 0

        G_max = 1.0 / d_min
        max_norm = int(G_max / np.sqrt(lambda_min_star)) + 1
        max_index = max_norm

        refs = []
        orbits = set()
        for h in range(-max_index, max_index + 1):
            for k in range(-max_index, max_index + 1):
                for l_idx in range(-max_index, max_index + 1):
                    if Crystal.hkl2tuple((h, k, l_idx)) in orbits or (
                        h == 0 and k == 0 and l_idx == 0
                    ):
                        continue
                    d = self.crystal.d_spacing((h, k, l_idx))
                    if d < d_min:
                        continue

                    th = np.arcsin(self.wavelength / (2 * d))
                    if np.isnan(th):
                        continue
                    twoth = 2 * np.degrees(th)
                    F, f_atoms = structure_factor(
                        self.crystal, (h, k, l_idx), th, self.wavelength
                    )
                    if self.multiplicity_mode == "metric":
                        mult, hkl_group = self.crystal.multiplicity_metric(
                            (h, k, l_idx),
                            max_index,
                            rtol=self.multiplicity_metric_rtol,
                            atol=self.multiplicity_metric_atol,
                        )
                    else:
                        mult, hkl_group = self.crystal.multiplicity((h, k, l_idx))
                    orbits.update(hkl_group)

                    hkl_name = hkl_group.pop()
                    hkl_name_pos = all(h >= 0 for h in hkl_name)
                    hkl_name_sqsum = (
                        hkl_name[0] ** 2 + hkl_name[1] ** 2 + hkl_name[2] ** 2
                    )
                    for hkl in hkl_group:
                        pos = all(h >= 0 for h in hkl)
                        sqsum = hkl[0] ** 2 + hkl[1] ** 2 + hkl[2] ** 2

                        if (
                            pos > hkl_name_pos
                            or pos == hkl_name_pos
                            and sqsum < hkl_name_sqsum
                            or pos == hkl_name_pos
                            and sqsum == hkl_name_sqsum
                            and array_weight(hkl) > array_weight(hkl_name)
                        ):
                            hkl_name = hkl
                            hkl_name_pos = pos
                            hkl_name_sqsum = sqsum

                    lf = l_factor(twotheta_deg=twoth)
                    pf = p_factor(twotheta_deg=twoth, thetam_deg=self.thetam_deg)
                    lpf = lf * pf
                    intensity = self.scale * mult * lpf * np.abs(F) ** 2
                    if intensity >= self.intensity_min:
                        refs.append(
                            {
                                "hkl": hkl_name,
                                "d": d,
                                "twotheta": twoth,
                                "mult": mult,
                                "l": lf,
                                "p": pf,
                                "lp": lpf,
                                "f_atoms": f_atoms,
                                "F": F,
                                "intensity": intensity,
                            }
                        )

        if self.normalize_intensity and refs:
            max_intensity = max(ref["intensity"] for ref in refs)
            if max_intensity > 0:
                for ref in refs:
                    ref["intensity"] = (
                        ref["intensity"] / max_intensity * self.intensity_max_value
                    )

        for ref in refs:
            ref["intensity_units"] = self.intensity_units
            if self.normalize_intensity:
                ref["intensity_units"] += " (normalized)"
        return refs

    def write_reflections_txt(self, filepath: Union[str, Path], refs=None) -> None:
        if refs is None:
            refs = self.reflections
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            crystal = self.crystal
            f.write("# Crystal metadata\n")
            f.write(f"# name: {self.name}\n")
            f.write(
                "# cell: "
                f"a={crystal.a:.6f}, b={crystal.b:.6f}, c={crystal.c:.6f}, "
                f"alpha={np.degrees(crystal.alpha):.6f}, "
                f"beta={np.degrees(crystal.beta):.6f}, "
                f"gamma={np.degrees(crystal.gamma):.6f}\n"
            )
            f.write(f"# volume: {crystal.V:.6f}\n")
            f.write(
                f"# wavelength: {self.wavelength:.6f} A; "
                f"twotheta_range: [{self.twotheta[0]:.6f}, {self.twotheta[-1]:.6f}] "
                f"step={self.twotheta[1] - self.twotheta[0]:.6f}\n"
            )
            f.write(
                f"# profile: {self.profile}; eta={self.eta}; "
                f"thetam_deg={self.thetam_deg}\n"
            )
            f.write(
                f"# caglioti: U={self.U}, V={self.V}, W={self.W}; scale={self.scale}\n"
            )
            f.write(
                f"# intensity: units={self.intensity_units}, "
                f"normalized={self.normalize_intensity}, "
                f"intensity_max_value={self.intensity_max_value}, "
                f"intensity_min={self.intensity_min}\n"
            )
            f.write(
                f"# multiplicity_mode: {self.multiplicity_mode}; "
                f"metric_rtol={self.multiplicity_metric_rtol}, "
                f"metric_atol={self.multiplicity_metric_atol}\n"
            )
            f.write(
                f"# spacegroup_ops: {len(crystal.spacegroup.operations)}; "
                f"atoms_input={len(crystal.atoms)}; atoms_full={len(crystal.full_atoms)}\n"
            )
            f.write("# atoms (element, x, y, z, occ, Biso)\n")
            for atom in crystal.atoms:
                x, y, z = atom.frac
                f.write(
                    f"#   {atom.element}, {x:.6f}, {y:.6f}, {z:.6f}, "
                    f"{atom.occ:.6f}, {atom.Biso:.6f}\n"
                )
            f_labels = atom_f_column_labels(crystal.full_atoms)
            f.write(
                "# f columns (one per atom in full_atoms, Waas–Kirfel f₀ at this 2θ): "
                + ", ".join(f_labels)
                + "\n"
            )
            f.write("#\n")

            # Фиксированная ширина в текстовой таблице: удобно читать глазами.
            cols = [
                ("n", 4, "right"),
                ("hkl", 9, "left"),
                ("d", 9, "right"),
                ("twotheta", 10, "right"),
                ("mult", 6, "right"),
                ("l", 9, "right"),
                *[(label, 9, "right") for label in f_labels],
                ("p", 9, "right"),
                ("F", 14, "right"),
                ("F^2", 14, "right"),
                ("intensity", 11, "right"),
            ]

            def _fmt(value, width, align):
                text = str(value)
                return text.ljust(width) if align == "left" else text.rjust(width)

            def _border():
                return "+" + "+".join("-" * (width + 2) for _, width, _ in cols) + "+"

            def _row(values):
                cells = [
                    _fmt(value, width, align)
                    for value, (_, width, align) in zip(values, cols)
                ]
                return "| " + " | ".join(cells) + " |"

            f.write(_border() + "\n")
            f.write(_row([name for name, _, _ in cols]) + "\n")
            f.write(_border() + "\n")

            for i, ref in enumerate(refs[::-1], start=1):
                hkl = ref["hkl"]
                row = [
                    f"{i}",
                    f"{hkl[0]} {hkl[1]} {hkl[2]}",
                    f"{ref['d']:.3f}",
                    f"{ref['twotheta']:.3f}",
                    f"{ref['mult']}",
                    f"{ref['l']:.3f}",
                    *[f"{fv:.3f}" for fv in ref["f_atoms"]],
                    f"{ref['p']:.3f}",
                    _format_F_tsv(ref["F"]),
                    _format_F_tsv(ref["F"] ** 2),
                    f"{ref['intensity']:.3f}",
                ]
                f.write(_row(row) + "\n")
            f.write(_border() + "\n")

    def write_reflections_json(self, filepath: Union[str, Path], refs=None) -> None:
        if refs is None:
            refs = self.reflections
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(refs, f, cls=NumpyEncoder)

    def write_metric_matrices(self, output_dir: Union[str, Path]) -> None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        np.savetxt(output_dir / "G.csv", self.crystal.G, delimiter=",")
        np.savetxt(output_dir / "Gstar.csv", self.crystal.Gstar, delimiter=",")

    def save_outputs(
        self,
        output_dir: Union[str, Path],
        *,
        txt: bool = True,
        json_file: Optional[bool] = None,
        metrics: bool = True,
        refs=None,
    ) -> None:
        """Запись результатов расчёта в каталог (CLI и ручной экспорт)."""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        if refs is None:
            refs = self.reflections
        if json_file is None:
            json_file = self.save_ref
        if txt:
            self.write_reflections_txt(output_dir / f"{self.name}.txt", refs=refs)
        if json_file:
            self.write_reflections_json(output_dir / f"{self.name}.json", refs=refs)
        if metrics:
            self.write_metric_matrices(output_dir)

    def save_refs(self, refs: Dict[str, float]):
        """Совместимость: сохранить в runs/<name>/ (как раньше)."""
        self.save_outputs(f"runs/{self.name}", refs=refs)

    def _convolve(self):
        y = np.zeros_like(self.twotheta)
        peak_dict = {}

        for ref in self.reflections:
            centre = ref["twotheta"]
            hkl = ref["hkl"]
            if centre < self.twotheta[0] or centre > self.twotheta[-1]:
                continue

            fwhm_rad = caglioti_fwhm(np.radians(centre / 2), self.U, self.V, self.W)
            fwhm_deg = np.degrees(fwhm_rad)
            intensity = ref["intensity"]

            if self.profile == "bar":
                bar = np.zeros_like(self.twotheta)
                idx = np.argmin(np.abs(self.twotheta - centre))
                bar[idx] = 1
                y_new = intensity * bar
            elif self.profile == "gaussian":
                y_new = intensity * gaussian(self.twotheta, centre, fwhm_deg)
            elif self.profile == "lorentzian":
                y_new = intensity * lorentzian(self.twotheta, centre, fwhm_deg)
            else:
                y_new = intensity * pseudo_voigt(
                    self.twotheta, centre, fwhm_deg, self.eta
                )

            y += y_new

            rounded_centre = round(centre, 3)
            pos = all(h >= 0 for h in hkl)
            sqsum = hkl[0] ** 2 + hkl[1] ** 2 + hkl[2] ** 2
            key = (not pos, sqsum, -intensity)

            if (rounded_centre not in peak_dict) or (
                key < peak_dict[rounded_centre][2]
            ):
                peak_dict[rounded_centre] = (hkl, intensity, key)

        # Профили с размытием нормированы на единичную площадь → пик ниже, чем у «палочки».
        # После свёртки снова вписываем максимум в intensity_max_value (как у bar).
        if self.normalize_intensity and self.profile != "bar":
            y_max_all = float(np.max(y))
            if y_max_all > 0:
                y = y * (self.intensity_max_value / y_max_all)

        hkl_labels = []
        for centre, (hkl, _, _) in peak_dict.items():
            idx = np.argmin(np.abs(self.twotheta - centre))
            y_max = y[idx]
            hkl_labels.append((hkl, centre, y_max))

        bg = np.polyval(self.bg_poly, self.twotheta)
        return y + bg, hkl_labels

    def generate_pattern(self):
        self.reflections = self._generate_reflections(d_min=self.wavelength / 2.0)
        self.ycalc, self.hkl_labels = self._convolve()

    def get_pattern_data(self):
        return self.twotheta, self.ycalc

    def set_params(self, **kwargs):
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise AttributeError(f"PowderPattern has no attribute '{key}'")
