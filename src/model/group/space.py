from typing import List

import numpy as np
import spglib

from ..atom.atom import Atom

symbol_to_number = {
    "H": 1,
    "He": 2,
    "Li": 3,
    "Be": 4,
    "B": 5,
    "C": 6,
    "N": 7,
    "O": 8,
    "F": 9,
    "Ne": 10,
    "Na": 11,
    "Mg": 12,
    "Al": 13,
    "Si": 14,
    "P": 15,
    "S": 16,
    "Cl": 17,
    "Ar": 18,
    "K": 19,
    "Ca": 20,
    "Sc": 21,
    "Ti": 22,
    "V": 23,
    "Cr": 24,
    "Mn": 25,
    "Fe": 26,
    "Co": 27,
    "Ni": 28,
    "Cu": 29,
    "Zn": 30,
    "Ga": 31,
    "Ge": 32,
    "As": 33,
    "Se": 34,
    "Br": 35,
    "Kr": 36,
    "Rb": 37,
    "Sr": 38,
    "Y": 39,
    "Zr": 40,
    "Nb": 41,
    "Mo": 42,
    "Tc": 43,
    "Ru": 44,
    "Rh": 45,
    "Pd": 46,
    "Ag": 47,
    "Cd": 48,
    "In": 49,
    "Sn": 50,
    "Sb": 51,
    "Te": 52,
    "I": 53,
    "Xe": 54,
    "Cs": 55,
    "Ba": 56,
    # ... можно добавить остальные
}


class SpaceGroup:
    def __init__(self, generators):
        self.generators = generators
        self.operations = self.generate_space_group(mod_lattice=False)
        self.lattice_operations = self.generate_space_group(mod_lattice=True)

    @staticmethod
    def from_spacegroup_number(number):
        spg_type = spglib.get_spacegroup_type(number)
        hall_number = spg_type.hall_number
        print(
            f"Hall number: {hall_number}\nSchoenflies: {spg_type.schoenflies}\nInternational: {spg_type.international_full}"
        )
        sym = spglib.get_symmetry_from_database(hall_number)
        rotations = sym["rotations"]
        translations = sym["translations"]

        generators = list(zip(rotations, translations))
        return SpaceGroup(generators)

    @staticmethod
    def from_structure(lattice: List[float], atoms: List[Atom], symprec: float = 1e-5):
        positions = [atom.frac for atom in atoms]
        numbers = [symbol_to_number.get(atom.element, 0) for atom in atoms]

        cell = (lattice, positions, numbers)
        symmetry = spglib.get_symmetry(cell=cell, symprec=symprec)
        rotations = symmetry["rotations"]
        translations = symmetry["translations"]

        generators = list(zip(rotations, translations))
        return SpaceGroup(generators)

    def generate_space_group(self, mod_lattice=False, tol=1e-8, max_elements=512):
        if not self.generators:
            dim = 3
        else:
            R0, _ = self.generators[0]
            dim = R0.shape[0]

        identity = np.eye(dim)
        zero = np.zeros(dim)

        def frac_part(t, mod_lattice=False):
            if not mod_lattice:
                return t - np.floor(t)
            return t

        def canonical(R, t):
            t_adj = frac_part(t, mod_lattice=mod_lattice)
            decimals = int(-np.log10(tol)) + 1
            R_rounded = np.round(R, decimals)
            t_rounded = np.round(t_adj, decimals)
            t_rounded = frac_part(t_rounded, mod_lattice=mod_lattice)
            R_tuple = tuple(tuple(row) for row in R_rounded)
            t_tuple = tuple(t_rounded)
            return (R_tuple, t_tuple)

        def compose(tr1, tr2):
            R1, t1 = tr1
            R2, t2 = tr2
            R = R1 @ R2
            t = R1 @ t2 + t1
            t = frac_part(t, mod_lattice=mod_lattice)
            return (R, t)

        def inverse(tr):
            R, t = tr
            R_inv = np.linalg.inv(R)
            t_inv = -R_inv @ t
            t_inv = frac_part(t_inv, mod_lattice=mod_lattice)
            return (R_inv, t_inv)

        elements = {}

        key_id = canonical(identity, zero)
        elements[key_id] = (identity.copy(), zero.copy())

        for R, t in self.generators:
            R = np.asarray(R)
            t = np.asarray(t)

            key = canonical(R, t)
            if key not in elements:
                elements[key] = (R.copy(), t.copy())

            R_inv, t_inv = inverse((R, t))
            key_inv = canonical(R_inv, t_inv)
            if key_inv not in elements:
                elements[key_inv] = (R_inv, t_inv)

        changed = True
        while changed and len(elements) <= max_elements:
            changed = False
            current = list(elements.values())
            n = len(current)
            for i in range(n):
                for j in range(n):
                    new_R, new_t = compose(current[i], current[j])
                    key = canonical(new_R, new_t)
                    if key not in elements:
                        elements[key] = (new_R, new_t)
                        changed = True
                        if len(elements) > max_elements:
                            return list(elements.values())

        return list(elements.values())

    @property
    def rotations(self):
        return [R for R, t in self.operations]

    @property
    def translations(self):
        return [t for R, t in self.operations]

    def apply(self, x, mod_lattice=False):
        ops = self.operations
        if mod_lattice:
            ops = self.lattice_operations
        positions = []
        for R, t in ops:
            x_new = R @ x + t
            positions.append(x_new)
        return positions
