import math
from typing import List

import numpy as np

from ..atom.atom import Atom


def canonical_frac(x, symprec: float = 1e-5) -> np.ndarray:
    """Дробные координаты в [0, 1); границы при symprec схлопываются в 0."""
    x = np.mod(np.asarray(x, dtype=float), 1.0)
    x = np.where(x < symprec, 0.0, x)
    x = np.where(x > 1.0 - symprec, 0.0, x)
    return x


def bravais_centering_translations(kind: str) -> List[tuple]:
    """
    Векторы центрирования в долях базисных векторов (a,b,c) для ортогональной
    конвенциональной ячейки (α=β=γ=90°): кубическая, тетрагональная, орторомбическая.

    P — примитивная; I — объёмно-центрированная (BCC); F — гранецентрированная (FCC);
    C — базоцентрированная (грань ab); A — грань bc; B — грань ac.
    """
    k = kind.strip().upper()
    if k == "P":
        return [(0.0, 0.0, 0.0)]
    if k == "I":
        return [(0.0, 0.0, 0.0), (0.5, 0.5, 0.5)]
    if k == "F":
        return [
            (0.0, 0.0, 0.0),
            (0.0, 0.5, 0.5),
            (0.5, 0.0, 0.5),
            (0.5, 0.5, 0.0),
        ]
    if k == "C":
        return [(0.0, 0.0, 0.0), (0.5, 0.5, 0.0)]
    if k == "A":
        return [(0.0, 0.0, 0.0), (0.0, 0.5, 0.5)]
    if k == "B":
        return [(0.0, 0.0, 0.0), (0.5, 0.0, 0.5)]
    raise ValueError(
        f"Неизвестный тип центрирования: {kind!r}; ожидается P, I, F, C, A или B"
    )


def expand_atoms_bravais_centering(
    atoms: List[Atom], kind: str, symprec: float = 1e-5
) -> List[Atom]:
    """
    Для каждого входного атома добавляет копии по векторам центрирования,
    удаляет дубликаты (тот же элемент и дробные координаты с периодом 1).
    """
    k = kind.strip().upper()
    if k in ("", "NONE"):
        return list(atoms)
    ts = bravais_centering_translations(k)
    out: List[Atom] = []
    for atom in atoms:
        for tx, ty, tz in ts:
            nf = canonical_frac(
                np.asarray(atom.frac, dtype=float)
                + np.array([tx, ty, tz], dtype=float),
                symprec,
            )
            new_atom = Atom(
                atom.element,
                float(nf[0]),
                float(nf[1]),
                float(nf[2]),
                atom.occ,
                atom.Biso,
            )
            duplicate = False
            for ex in out:
                if ex.element == new_atom.element and frac_periodic_allclose(
                    ex.frac, new_atom.frac, atol=symprec
                ):
                    duplicate = True
                    break
            if not duplicate:
                out.append(new_atom)
    return out


def expand_atoms_cubic_centering(
    atoms: List[Atom], kind: str, symprec: float = 1e-5
) -> List[Atom]:
    """Совместимость: то же, что expand_atoms_bravais_centering."""
    return expand_atoms_bravais_centering(atoms, kind, symprec=symprec)


def frac_periodic_allclose(a, b, atol: float = 1e-5) -> bool:
    """Сравнение дробных координат с периодом 1 (0 и 1 — одна точка)."""
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = np.abs(a - b)
    d = np.minimum(d, 1.0 - d)
    return bool(np.all(d < atol))


def generate_hkl_by_layer(n, include_zero=False):
    result = []
    s = 0
    while len(result) < n:
        max_h = int(math.isqrt(s))
        for h in range(-max_h, max_h + 1):
            h2 = h * h
            if h2 > s:
                continue
            rem = s - h2
            max_k = int(math.isqrt(rem))
            for k in range(-max_k, max_k + 1):
                k2 = k * k
                if k2 > rem:
                    continue
                l2 = rem - k2
                l_val = int(math.isqrt(l2))
                if l_val * l_val == l2:
                    # Нашли целое l (неотрицательное)
                    if l_val == 0:
                        if not (h == 0 and k == 0 and not include_zero):
                            result.append((h, k, 0))
                    else:
                        result.append((h, k, l_val))
                        result.append((h, k, -l_val))
        s += 1
    return result[:n]
