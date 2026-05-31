import math
from typing import List

import numpy as np

from ..atom.atom import Atom


def canonical_frac(x, symprec: float = 1e-5) -> np.ndarray:
    """Приводит дробные координаты к каноническому виду в [0, 1).

    Границы при ``symprec`` схлопываются в 0.

    Args:
        x: Дробные координаты (скаляр или массив).
        symprec: Допуск для схлопывания границ 0 и 1.

    Returns:
        Массив координат в диапазоне [0, 1).
    """
    x = np.mod(np.asarray(x, dtype=float), 1.0)
    x = np.where(x < symprec, 0.0, x)
    x = np.where(x > 1.0 - symprec, 0.0, x)
    return x


def bravais_centering_translations(kind: str) -> List[tuple]:
    """Возвращает векторы центрирования Браве для ортогональной ячейки.

    Векторы задаются в долях базисных векторов (a, b, c) при α=β=γ=90°.

    Args:
        kind: Тип центрирования: P, I, F, C, A или B.

    Returns:
        Список кортежей (tx, ty, tz) — сдвиги в долях ячейки.

    Raises:
        ValueError: Если тип центрирования не распознан.
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
    """Разворачивает атомы по векторам центрирования Браве.

    Args:
        atoms: Список атомов элементарной ячейки.
        kind: Тип центрирования (P, I, F, C, A, B или none).
        symprec: Допуск при сравнении дробных координат.

    Returns:
        Расширенный список атомов без дубликатов (один элемент + одна позиция).
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
    """Разворачивает атомы по центрированию (алиас ``expand_atoms_bravais_centering``).

    Args:
        atoms: Список атомов элементарной ячейки.
        kind: Тип центрирования.
        symprec: Допуск при сравнении координат.

    Returns:
        Расширенный список атомов.
    """
    return expand_atoms_bravais_centering(atoms, kind, symprec=symprec)


def frac_periodic_allclose(a, b, atol: float = 1e-5) -> bool:
    """Сравнивает дробные координаты с учётом периодичности 1.

    Args:
        a: Первая координата (массив).
        b: Вторая координата (массив).
        atol: Абсолютный допуск по каждой компоненте.

    Returns:
        ``True``, если координаты эквивалентны с периодом 1.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    d = np.abs(a - b)
    d = np.minimum(d, 1.0 - d)
    return bool(np.all(d < atol))


def generate_hkl_by_layer(n, include_zero=False):
    """Генерирует n индексов Миллера, упорядоченных по возрастанию h²+k²+l².

    Args:
        n: Число требуемых отражений.
        include_zero: Включать ли отражение (0, 0, 0).

    Returns:
        Список кортежей (h, k, l) длины не более ``n``.
    """
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
