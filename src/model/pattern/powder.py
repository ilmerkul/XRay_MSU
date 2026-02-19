import numpy as np

from ..crystal.structure import structure_factor
from ..group.space import multiplicity
from .utils import caglioti_fwhm, gaussian, lorentzian, lp_factor, pseudo_voigt


# ----------------------------------------------------------------------
# 6. Powder pattern simulation
# ----------------------------------------------------------------------
class PowderPattern:
    def __init__(
        self,
        crystal,
        wavelength,
        twotheta_range,
        U=0.01,
        V=-0.01,
        W=0.005,
        scale=1.0,
        profile="pvoigt",
        eta=0.5,
        bg_poly=None,
    ):
        self.crystal = crystal
        self.wavelength = wavelength
        self.twotheta = np.arange(
            twotheta_range[0], twotheta_range[1], twotheta_range[2]
        )
        self.U, self.V, self.W = U, V, W
        self.scale = scale
        self.profile = profile
        self.eta = eta
        self.bg_poly = bg_poly if bg_poly is not None else [0, 0, 0]

        self.reflections = self._generate_reflections(d_min=0.8)
        self.ycalc = self._convolve()

    def _generate_reflections(self, d_min):
        hmax = int(max(self.crystal.a, self.crystal.b, self.crystal.c) / d_min) + 1
        refs = []
        for h in range(-hmax, hmax + 1):
            for k in range(-hmax, hmax + 1):
                for l in range(-hmax, hmax + 1):
                    if h == 0 and k == 0 and l == 0:
                        continue
                    d = self.crystal.d_spacing((h, k, l))
                    if d >= d_min:
                        th = np.arcsin(self.wavelength / (2 * d))
                        if np.isnan(th):
                            continue
                        twoth = 2 * np.degrees(th)
                        F = structure_factor(self.crystal, (h, k, l), self.wavelength)
                        mult = multiplicity((h, k, l), self.crystal)
                        lp = lp_factor(twoth)
                        intensity = self.scale * mult * lp * np.abs(F) ** 2
                        if intensity > 1e-6:  # skip negligible peaks
                            refs.append(
                                {
                                    "hkl": (h, k, l),
                                    "d": d,
                                    "twotheta": twoth,
                                    "F": F,
                                    "intensity": intensity,
                                }
                            )
        return refs

    def _convolve(self):
        y = np.zeros_like(self.twotheta)
        for ref in self.reflections:
            centre = ref["twotheta"]
            if centre < self.twotheta[0] or centre > self.twotheta[-1]:
                continue
            fwhm_rad = caglioti_fwhm(np.radians(centre / 2), self.U, self.V, self.W)
            fwhm_deg = np.degrees(fwhm_rad)
            intensity = ref["intensity"]
            if self.profile == "gaussian":
                y += intensity * gaussian(self.twotheta, centre, fwhm_deg)
            elif self.profile == "lorentzian":
                y += intensity * lorentzian(self.twotheta, centre, fwhm_deg)
            else:  # pseudo-Voigt
                y += intensity * pseudo_voigt(self.twotheta, centre, fwhm_deg, self.eta)
        # Add background
        bg = np.polyval(self.bg_poly, self.twotheta)
        return y + bg
