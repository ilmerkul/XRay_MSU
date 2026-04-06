import math

import numpy as np


def canonical_frac(x, symprec: float = 1e-5) -> np.ndarray:
    """Дробные координаты в [0, 1); границы при symprec схлопываются в 0."""
    x = np.mod(np.asarray(x, dtype=float), 1.0)
    x = np.where(x < symprec, 0.0, x)
    x = np.where(x > 1.0 - symprec, 0.0, x)
    return x


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
                l = int(math.isqrt(l2))
                if l * l == l2:
                    # Нашли целое l (неотрицательное)
                    if l == 0:
                        if not (h == 0 and k == 0 and not include_zero):
                            result.append((h, k, 0))
                    else:
                        result.append((h, k, l))
                        result.append((h, k, -l))
        s += 1
    return result[:n]
