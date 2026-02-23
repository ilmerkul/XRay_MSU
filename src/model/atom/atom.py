import numpy as np


class Atom:
    def __init__(self, element, x, y, z, occ=1.0, Biso=1.0):
        self.element = element
        self.frac = np.array([x, y, z])
        self.occ = occ
        self.Biso = Biso
