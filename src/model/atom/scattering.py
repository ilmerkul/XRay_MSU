import xraylib


def atomic_number(element):
    return xraylib.SymbolToAtomicNumber(element)


def f0(element, s):
    """
    Atomic scattering factor f0(s) for given element at sin(theta)/lambda = s.
    Uses xraylib.FF_Rayl (relativistic Hartree-Fock).
    """
    Z = atomic_number(element)
    # xraylib.FF_Rayl expects q = sin(theta)/lambda in Å⁻¹
    return xraylib.FF_Rayl(Z, s)
