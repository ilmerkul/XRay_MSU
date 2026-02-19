import numpy as np

# ----------------------------------------------------------------------
# 1. Atomic scattering factors (Cromer-Mann coefficients)
# ----------------------------------------------------------------------
SCATTERING_FACTORS = {
    "Si": {
        "a": [2.275, 2.4278, 1.4369, 0.7857],
        "b": [2.6058, 24.8363, 70.8085, 161.6929],
        "c": 0.2172,
    },
    "O": {
        "a": [3.0485, 2.2868, 1.5463, 0.867],
        "b": [13.2771, 5.7011, 0.3239, 32.9089],
        "c": 0.2508,
    },
    "Al": {
        "a": [4.1745, 2.6176, 1.9553, 1.1935],
        "b": [1.8584, 9.4695, 53.2539, 180.5347],
        "c": 0.2891,
    },
}


def f0(element, s):
    """Cromer-Mann f0 for given element at sin(theta)/lambda = s."""
    coeff = SCATTERING_FACTORS[element]
    s2 = s * s
    total = coeff["c"]
    for a, b in zip(coeff["a"], coeff["b"]):
        total += a * np.exp(-b * s2)
    return total
