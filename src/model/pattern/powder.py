import csv
import json
import os
from typing import Dict

import numpy as np

from ..crystal.crystal import Crystal
from ..crystal.structure import structure_factor
from .utils import (
    NumpyEncoder,
    array_weight,
    caglioti_fwhm,
    gaussian,
    l_factor,
    lorentzian,
    p_factor,
    pseudo_voigt,
)


class PowderPattern:
    def __init__(
        self,
        name: str,
        crystal: Crystal,
        wavelength: float,
        twotheta_range: np.ndarray,
        thetam_deg: float,
        U: float = 0.01,
        V: float = -0.01,
        W: float = 0.005,
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
        self.profile = profile
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
                for l in range(-max_index, max_index + 1):
                    if Crystal.hkl2tuple((h, k, l)) in orbits or (
                        h == 0 and k == 0 and l == 0
                    ):
                        continue
                    d = self.crystal.d_spacing((h, k, l))
                    if d < d_min:
                        continue

                    th = np.arcsin(self.wavelength / (2 * d))
                    if np.isnan(th):
                        continue
                    twoth = 2 * np.degrees(th)
                    F = structure_factor(self.crystal, (h, k, l), th, self.wavelength)
                    if self.multiplicity_mode == "metric":
                        mult, hkl_group = self.crystal.multiplicity_metric(
                            (h, k, l),
                            max_index,
                            rtol=self.multiplicity_metric_rtol,
                            atol=self.multiplicity_metric_atol,
                        )
                    else:
                        mult, hkl_group = self.crystal.multiplicity((h, k, l))
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
        self.save_refs(refs)
        return refs

    def save_refs(self, refs: Dict[str, float]):
        os.makedirs(f"runs/{self.name}", exist_ok=True)

        if self.save_ref:
            with open(f"runs/{self.name}/{self.name}.json", "w") as f:
                json.dump(refs, f, cls=NumpyEncoder)

        with open(
            f"runs/{self.name}/{self.name}.tsv", "w", newline="", encoding="utf-8"
        ) as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerow(list(refs[0].keys()))

            for ref in refs[::-1]:
                hkl = ref["hkl"]
                d = ref["d"]
                twotheta = ref["twotheta"]
                mult = ref["mult"]
                l = ref["l"]
                p = ref["p"]
                lp = ref["lp"]
                F = ref["F"]
                intensity = ref["intensity"]

                writer.writerow(
                    [
                        f"{hkl[0]} {hkl[1]} {hkl[2]}",
                        f"{d:.3f}",
                        f"{twotheta:.3f}",
                        mult,
                        f"{l:.3f}",
                        f"{p:.3f}",
                        f"{lp:.3f}",
                        f"{F:.3f}",
                        f"{intensity:.3f}",
                    ]
                )

        np.savetxt(f"runs/{self.name}/G.csv", self.crystal.G, delimiter=",")
        np.savetxt(f"runs/{self.name}/Gstar.csv", self.crystal.Gstar, delimiter=",")

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

            if self.profile == "stick":
                stick = np.zeros_like(self.twotheta)
                idx = np.argmin(np.abs(self.twotheta - centre))
                stick[idx] = 1
                y_new = intensity * stick
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
