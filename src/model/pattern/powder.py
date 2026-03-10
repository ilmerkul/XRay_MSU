import numpy as np

from ..crystal.structure import structure_factor
from ..group.space import multiplicity
from .utils import caglioti_fwhm, gaussian, lorentzian, lp_factor, pseudo_voigt


class PowderPattern:
    def __init__(
        self,
        name,
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
        self.name = name
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

        self.reflections = self._generate_reflections(d_min=self.wavelength / 2.0)
        self.ycalc, self.hkl_labels = self._convolve()

    def _generate_reflections(self, d_min):
        # ---- FIX: Use reciprocal metric tensor Gstar ----
        Gstar = self.crystal.Gstar
        eigvals = np.linalg.eigvalsh(Gstar)
        lambda_max_star = np.max(eigvals)   # largest eigenvalue of Gstar

        if lambda_max_star <= 0:   # fallback (should not happen for a real crystal)
            a, b, c = self.crystal.a, self.crystal.b, self.crystal.c
            max_index = int(max(a, b, c) / d_min) * 2 + 5
        else:
            G_max = 1.0 / d_min
            # Safe Euclidean norm bound: |h| ≤ G_max / sqrt(lambda_max_star)
            max_norm = int(np.sqrt(G_max**2 / lambda_max_star)) + 1
            max_index = max_norm
        # -------------------------------------------------

        refs = []
        for h in range(-max_index, max_index + 1):
            for k in range(-max_index, max_index + 1):
                for l in range(-max_index, max_index + 1):
                    if h == 0 and k == 0 and l == 0:
                        continue
                    d = self.crystal.d_spacing((h, k, l))
                    if d >= d_min:
                        th = np.arcsin(self.wavelength / (2 * d))
                        if np.isnan(th):
                            continue
                        twoth = 2 * np.degrees(th)
                        F = structure_factor(
                            self.crystal, (h, k, l), th, self.wavelength
                        )
                        mult = multiplicity(self.crystal, (h, k, l))
                        print(h, k, l, twoth)
                        lp = lp_factor(twoth)
                        #intensity = self.scale * mult * lp * np.abs(F) ** 2
                        intensity = self.scale  * lp * np.abs(F) ** 2
                        if intensity > 1e-6:
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
        # Словарь для группировки: ключ – округлённый угол, значение – (hkl, интенсивность)
        peak_dict = {}

        for ref in self.reflections:
            centre = ref["twotheta"]
            hkl = ref["hkl"]
            if centre < self.twotheta[0] or centre > self.twotheta[-1]:
                continue

            fwhm_rad = caglioti_fwhm(np.radians(centre / 2), self.U, self.V, self.W)
            fwhm_deg = np.degrees(fwhm_rad)
            intensity = ref["intensity"]

            # Вычисляем вклад пика
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
                y_new = intensity * pseudo_voigt(self.twotheta, centre, fwhm_deg, self.eta)

            y += y_new
            
            # Группировка: округляем угол до 3 знаков (можно менять точность)
            rounded_centre = round(centre, 3)
            # Сохраняем отражение с максимальной интенсивностью для данного угла
            if rounded_centre not in peak_dict or intensity > peak_dict[rounded_centre][1]:
                peak_dict[rounded_centre] = (hkl, intensity)

        # Формируем список подписей: для каждого пика берём его максимум из y
        hkl_labels = []
        for centre, (hkl, _) in peak_dict.items():
            # Находим индекс, ближайший к centre
            idx = np.argmin(np.abs(self.twotheta - centre))
            y_max = y[idx]
            hkl_labels.append((hkl, centre, y_max))

        bg = np.polyval(self.bg_poly, self.twotheta)
        return y + bg, hkl_labels