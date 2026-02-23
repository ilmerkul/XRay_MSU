import numpy as np

from ..atom.scattering import f0


def structure_factor(crystal, hkl, wavelength):
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return 0.0
    s_val = 0.5 / d  # sinθ/λ
    F = 0.0 + 0.0j
    for atom in crystal.full_atoms:
        phase = 2j * np.pi * np.dot(hkl, atom.frac)
        f = f0(atom.element, s_val)
        T = np.exp(-atom.Biso * s_val**2)
        F += atom.occ * f * T * np.exp(phase)
    return F


def theta(hkl, crystal, wavelength):
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return np.nan
    sinth = wavelength / (2 * d)
    if sinth > 1:
        return np.nan
    return np.arcsin(sinth)
