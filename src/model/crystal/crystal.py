import numpy as np
import spglib

from ..atom.atom import Atom


def lattice_to_matrix(a, b, c, alpha, beta, gamma):
    alpha = np.radians(alpha)
    beta = np.radians(beta)
    gamma = np.radians(gamma)
    ca = np.cos(alpha)
    cb = np.cos(beta)
    cg = np.cos(gamma)
    sg = np.sin(gamma)

    a_vec = [a, 0.0, 0.0]
    b_vec = [b * cg, b * sg, 0.0]
    cx = c * cb
    cy = c * (ca - cb * cg) / sg
    cz = c * np.sqrt(1.0 - cb**2 - ((ca - cb * cg) / sg) ** 2)
    c_vec = [cx, cy, cz]
    return np.array([a_vec, b_vec, c_vec])


class Crystal:
    def __init__(
        self, a, b, c, alpha, beta, gamma, spacegroup_number, atoms, symprec=1e-5
    ):
        self.a = a
        self.b = b
        self.c = c
        self.alpha = np.radians(alpha)
        self.beta = np.radians(beta)
        self.gamma = np.radians(gamma)
        self.spacegroup_number = spacegroup_number
        self.atoms = atoms
        self.symprec = symprec

        self._compute_metrics()
        self._lattice_matrix = lattice_to_matrix(a, b, c, alpha, beta, gamma)

        self.rotations, self.translations = self._get_symmetry_operations()

        self.full_atoms = self._generate_full_atoms()

    def _compute_metrics(self):
        ca = np.cos(self.alpha)
        cb = np.cos(self.beta)
        cg = np.cos(self.gamma)
        self.G = np.array(
            [
                [self.a**2, self.a * self.b * cg, self.a * self.c * cb],
                [self.a * self.b * cg, self.b**2, self.b * self.c * ca],
                [self.a * self.c * cb, self.b * self.c * ca, self.c**2],
            ]
        )
        self.V = (
            self.a
            * self.b
            * self.c
            * np.sqrt(1 - ca**2 - cb**2 - cg**2 + 2 * ca * cb * cg)
        )
        self.Gstar = np.linalg.inv(self.G)

    def _get_symmetry_operations(self):
        try:
            spg_type = spglib.get_spacegroup_type(self.spacegroup_number)
            hall_number = spg_type.hall_number
            sym = spglib.get_symmetry_from_database(hall_number)
            rotations = sym['rotations']
            translations = sym['translations']
            return rotations, translations
        except (AttributeError, KeyError, RuntimeError) as e:
            raise RuntimeError(
                f"Could not get symmetry operations for space group {self.spacegroup_number}. "
                "Ensure spglib is up‑to‑date and the space group number is valid."
            ) from e

    def _generate_full_atoms(self):
        full = []
        for atom in self.atoms:
            for R, t in zip(self.rotations, self.translations):
                new_frac = R @ atom.frac + t
                new_frac = new_frac % 1.0
                duplicate = False
                for existing in full:
                    if existing.element != atom.element:
                        continue
                    if np.allclose(existing.frac, new_frac, atol=self.symprec):
                        duplicate = True
                        break
                if not duplicate:
                    new_atom = Atom(
                        atom.element,
                        new_frac[0],
                        new_frac[1],
                        new_frac[2],
                        atom.occ,
                        atom.Biso,
                    )
                    full.append(new_atom)
        return full

    def d_spacing(self, hkl):
        h = np.array(hkl, dtype=float)
        invd2 = np.dot(h, np.dot(self.Gstar, h))
        if invd2 <= 0:
            return np.inf
        return 1.0 / np.sqrt(invd2)

    def copy(self):
        new_crystal = Crystal(
            self.a,
            self.b,
            self.c,
            np.degrees(self.alpha),
            np.degrees(self.beta),
            np.degrees(self.gamma),
            self.spacegroup_number,
            self.atoms,
            self.symprec,
        )
        return new_crystal