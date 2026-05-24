from math import pi, sin
from typing import List, Tuple

import numpy as np
import xraylib

from ..crystal.crystal import Crystal


def _f_scalar_for_output(f_total) -> float:
    """Скаляр f для таблицы: вещественный f₀ или |f| при комплексном f."""
    if isinstance(f_total, complex):
        return float(abs(f_total))
    return float(f_total)


def atom_f_column_labels(atoms) -> List[str]:
    """Имена столбцов f_<Element>_<n> в порядке full_atoms."""
    counts = {}
    labels = []
    for atom in atoms:
        elem = atom.element
        counts[elem] = counts.get(elem, 0) + 1
        labels.append(f"f_{elem}_{counts[elem]}")
    return labels


def structure_factor(
    crystal: Crystal,
    hkl: Tuple[float],
    th: float,
    wavelength: float,
    local: bool = True,
):
    """
    Вычисляет структурный фактор F(hkl) с учётом аномальной дисперсии.

    Параметры
    ----------
    crystal : Crystal
        Объект кристалла с полным списком атомов (full_atoms).
    hkl : tuple
        Индексы Миллера (h, k, l).
    th : float
        Угол Брэгга в радианах.
    wavelength : float
        Длина волны рентгеновского излучения (в тех же единицах, что и длина волны).

    Возвращает
    -------
    F : complex
        Структурный фактор F = Σ occ * (f0 + f' + i f'') * T * exp(2πi (h·x))
    f_atoms : list of float
        Атомные амплитуды f_j (по одной на каждый атом full_atoms, в том же порядке).
    """
    s_val = sin(th) / wavelength
    F = 0.0 + 0.0j
    f_atoms: List[float] = []

    for atom in crystal.full_atoms:
        if local:
            f_total = crystal.asf.get_f0_from_theta_lambda(
                symbol=atom.element, theta_deg=th * 180 / pi, lambda_ang=wavelength
            )
        else:
            z = xraylib.SymbolToAtomicNumber(atom.element)
            f0 = xraylib.FF_Rayl(z, s_val)
            energy_keV = 12.398 / wavelength
            f_prime = xraylib.Fi(z, energy_keV)
            f_double_prime = xraylib.Fii(z, energy_keV)
            f_total = f0 + f_prime + 1j * f_double_prime

        f_atoms.append(_f_scalar_for_output(f_total))

        T = np.exp(-atom.Biso * s_val**2)
        phase = 2j * np.pi * np.dot(hkl, atom.frac)
        F += atom.occ * f_total * T * np.exp(phase)

    return F, f_atoms


def theta(hkl, crystal, wavelength):
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return np.nan
    sinth = wavelength / (2 * d)
    if sinth > 1:
        return np.nan
    return np.arcsin(sinth)
