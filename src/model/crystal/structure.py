from math import sin, pi
from typing import Tuple

import numpy as np
import xraylib

from ..crystal.crystal import Crystal


def structure_factor(crystal: Crystal, hkl: Tuple[float], th: float, wavelength: float, local: bool=True):
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
    complex
        Структурный фактор F = Σ occ * (f0 + f' + i f'') * T * exp(2πi (h·x))
    """
    s_val = sin(th) / wavelength
    F = 0.0 + 0.0j

    for atom in crystal.full_atoms:
        if local:
            f_total = crystal.asf.get_f0_from_theta_lambda(symbol=atom.element, 
                                                           theta_deg=th * 180 / pi, 
                                                           lambda_ang=wavelength)
        else:
            f0 = xraylib.FF_Rayl(xraylib.SymbolToAtomicNumber(atom.element), s_val)

            energy_keV = 12.398 / wavelength
            f_prime = xraylib.Fi(xraylib.SymbolToAtomicNumber(atom.element), energy_keV)
            f_double_prime = xraylib.Fii(
                xraylib.SymbolToAtomicNumber(atom.element), energy_keV
            )

            f_total = f0 + f_prime + 1j * f_double_prime

        T = np.exp(-atom.Biso * s_val**2)

        phase = 2j * np.pi * np.dot(hkl, atom.frac)

        F += atom.occ * f_total * T * np.exp(phase)

    return F


def theta(hkl, crystal, wavelength):
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return np.nan
    sinth = wavelength / (2 * d)
    if sinth > 1:
        return np.nan
    return np.arcsin(sinth)
