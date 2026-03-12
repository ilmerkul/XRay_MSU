import json

import numpy as np

from ..crystal.crystal import Crystal
from ..crystal.structure import structure_factor
from .utils import caglioti_fwhm, gaussian, lorentzian, lp_factor, pseudo_voigt


class NumpyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.complex128) or isinstance(obj, complex):
            return {"real": obj.real, "imag": obj.imag}
        return super().default(obj)


def array_weight(arr):
    """
    Возвращает вес массива, равный числу инверсий.
    Чем ближе массив к обратному порядку, тем больше вес.
    """

    # Вспомогательная рекурсивная функция сортировки слиянием,
    # которая попутно подсчитывает инверсии.
    def merge_count_inv(subarr):
        if len(subarr) <= 1:
            return subarr, 0
        mid = len(subarr) // 2
        left, inv_left = merge_count_inv(subarr[:mid])
        right, inv_right = merge_count_inv(subarr[mid:])
        merged = []
        i = j = 0
        inv = inv_left + inv_right
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                merged.append(left[i])
                i += 1
            else:
                merged.append(right[j])
                # Все оставшиеся элементы left[i:] больше right[j]
                inv += len(left) - i
                j += 1
        merged.extend(left[i:])
        merged.extend(right[j:])
        return merged, inv

    _, inversions = merge_count_inv(arr)
    return inversions


class PowderPattern:
    def __init__(
        self,
        name,
        crystal: Crystal,
        wavelength,
        twotheta_range,
        U=0.01,
        V=-0.01,
        W=0.005,
        scale=1.0,
        profile="pvoigt",
        eta=0.5,
        bg_poly=None,
        intensity_units="arbitrary",
        normalize_intensity=True,
        intensity_max_value=100.0,
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
        self.intensity_units = intensity_units
        self.normalize_intensity = normalize_intensity
        self.intensity_max_value = intensity_max_value

        self.reflections = self._generate_reflections(d_min=self.wavelength / 2.0)
        self.ycalc, self.hkl_labels = self._convolve()

    def _generate_reflections(self, d_min):
        # ---- FIX: Use reciprocal metric tensor Gstar ----
        Gstar = self.crystal.Gstar
        eigvals = np.linalg.eigvalsh(Gstar)
        lambda_max_star = np.max(eigvals)  # largest eigenvalue of Gstar

        if lambda_max_star <= 0:  # fallback (should not happen for a real crystal)
            a, b, c = self.crystal.a, self.crystal.b, self.crystal.c
            max_index = int(max(a, b, c) / d_min) * 2 + 5
        else:
            G_max = 1.0 / d_min
            # Safe Euclidean norm bound: |h| ≤ G_max / sqrt(lambda_max_star)
            max_norm = int(np.sqrt(G_max**2 / lambda_max_star)) + 1
            max_index = max_norm
        # -------------------------------------------------

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
                    if d >= d_min:
                        th = np.arcsin(self.wavelength / (2 * d))
                        if np.isnan(th):
                            continue
                        twoth = 2 * np.degrees(th)
                        F = structure_factor(
                            self.crystal, (h, k, l), th, self.wavelength
                        )
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

                        lp = lp_factor(twoth)
                        intensity = self.scale * mult * lp * np.abs(F) ** 2
                        if intensity > 1e-6:
                            refs.append(
                                {
                                    "hkl": hkl_name,
                                    "d": d,
                                    "twotheta": twoth,
                                    "mult": mult,
                                    "lp": lp,
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

        with open(f"images/{self.name}.json", "w") as f:
            json.dump(refs, f, cls=NumpyEncoder)
        return refs

    def _convolve(self):
        y = np.zeros_like(self.twotheta)
        # Словарь для группировки: ключ – округлённый угол, значение – (hkl, интенсивность, ключ_сравнения)
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
                y_new = intensity * pseudo_voigt(
                    self.twotheta, centre, fwhm_deg, self.eta
                )

            y += y_new

            # Группировка: округляем угол до 3 знаков
            rounded_centre = round(centre, 3)

            # Вычисляем ключ для сравнения отражений:
            #  - сначала предпочитаем те, у которых все индексы неотрицательные
            #  - затем наименьшую сумму квадратов индексов
            #  - при равенстве – бо́льшую интенсивность
            pos = all(h >= 0 for h in hkl)
            sqsum = hkl[0] ** 2 + hkl[1] ** 2 + hkl[2] ** 2
            # not pos: False для положительных, True для остальных – значит положительные имеют меньший ключ
            key = (not pos, sqsum, -intensity)

            # Сохраняем отражение с наилучшим ключом для данного угла
            if (rounded_centre not in peak_dict) or (
                key < peak_dict[rounded_centre][2]
            ):
                peak_dict[rounded_centre] = (hkl, intensity, key)

        # Формируем список подписей: для каждого пика берём его максимум из y
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
