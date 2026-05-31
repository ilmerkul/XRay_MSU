from math import pi, sin
from typing import List, Tuple

import numpy as np

from ..crystal.crystal import Crystal


def _f_scalar_for_output(f_total) -> float:
    """Преобразует атомный фактор в скаляр для вывода в таблицу.

    Args:
        f_total: Вещественный f₀ или комплексный f = f₀ + f' + i f''.

    Returns:
        Вещественная часть или модуль комплексного значения.
    """
    if isinstance(f_total, complex):
        return float(abs(f_total))
    return float(f_total)


def _atomic_f_xraylib(symbol: str, s_val: float, wavelength: float) -> complex:
    """Атомный f через xraylib (f₀ + f' + i f'').

    Args:
        symbol: Символ элемента.
        s_val: sin(θ)/λ (Å⁻¹).
        wavelength: Длина волны (Å).

    Raises:
        ImportError: Если пакет xraylib не установлен.
    """
    try:
        import xraylib
    except ImportError as e:
        raise ImportError(
            "Для --no-local нужен пакет xraylib: uv sync --extra xraylib"
        ) from e

    z = xraylib.SymbolToAtomicNumber(symbol)
    f0 = xraylib.FF_Rayl(z, s_val)
    energy_keV = 12.398 / wavelength
    f_prime = xraylib.Fi(z, energy_keV)
    f_double_prime = xraylib.Fii(z, energy_keV)
    return f0 + f_prime + 1j * f_double_prime


def atom_f_element_labels(atoms) -> List[str]:
    """Имена столбцов f_<Element> — по одному на тип элемента.

    Args:
        atoms: Список атомов (обычно ``crystal.full_atoms``).

    Returns:
        Уникальные метки в порядке первого появления элемента.
    """
    seen: List[str] = []
    for atom in atoms:
        if atom.element not in seen:
            seen.append(atom.element)
    return [f"f_{elem}" for elem in seen]


def f_values_by_element(f_atoms: List[float], atoms) -> dict[str, float]:
    """Сопоставляет f_j первому атому каждого типа элемента.

    Args:
        f_atoms: Значения f по ``full_atoms``.
        atoms: Список атомов в том же порядке.

    Returns:
        Словарь ``element -> f`` (без дублирования по позициям).
    """
    out: dict[str, float] = {}
    for fv, atom in zip(f_atoms, atoms):
        if atom.element not in out:
            out[atom.element] = fv
    return out


def atom_f_column_labels(atoms) -> List[str]:
    """Формирует имена столбцов f_<Element>_<n> для таблицы отражений.

    Args:
        atoms: Список атомов (обычно ``crystal.full_atoms``).

    Returns:
        Метки столбцов в порядке атомов.
    """
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
    """Вычисляет структурный фактор F(hkl) с учётом аномальной дисперсии.

    Args:
        crystal: Кристалл с заполненным ``full_atoms``.
        hkl: Индексы Миллера (h, k, l).
        th: Угол Брэгга в радианах.
        wavelength: Длина волны рентгеновского излучения (Å).
        local: Если ``True``, таблица Waas–Kirfel; иначе xraylib (extra).

    Returns:
        Кортеж ``(F, f_atoms)``, где ``F`` — комплексный структурный фактор,
        ``f_atoms`` — список скalarных f_j по каждому атому ``full_atoms``.
    """
    s_val = sin(th) / wavelength
    theta_deg = th * 180 / pi
    hkl_arr = np.asarray(hkl, dtype=float)
    f_cache: dict[str, float | complex] = {}
    F = 0.0 + 0.0j
    f_atoms: List[float] = []

    for atom in crystal.full_atoms:
        if local:
            elem = atom.element
            if elem not in f_cache:
                f_cache[elem] = crystal.asf.get_f0_from_theta_lambda(
                    symbol=elem, theta_deg=theta_deg, lambda_ang=wavelength
                )
            f_total = f_cache[elem]
        else:
            f_total = _atomic_f_xraylib(atom.element, s_val, wavelength)

        f_atoms.append(_f_scalar_for_output(f_total))

        T = np.exp(-atom.Biso * s_val**2)
        phase = 2j * np.pi * np.dot(hkl_arr, atom.frac)
        F += atom.occ * f_total * T * np.exp(phase)

    return F, f_atoms


def theta(hkl, crystal, wavelength):
    """Вычисляет угол Брэгга для отражения (hkl).

    Args:
        hkl: Индексы Миллера.
        crystal: Объект кристалла.
        wavelength: Длина волны (Å).

    Returns:
        Угол Брэгга в радианах или ``nan``, если отражение недостижимо.
    """
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return np.nan
    sinth = wavelength / (2 * d)
    if sinth > 1:
        return np.nan
    return np.arcsin(sinth)
