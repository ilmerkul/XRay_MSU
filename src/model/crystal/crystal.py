import numpy as np
import spglib

from ..atom.atom import Atom


def lattice_to_matrix(a, b, c, alpha, beta, gamma):
    """Convert lattice parameters to a 3x3 matrix (rows = basis vectors)."""
    alpha = np.radians(alpha)
    beta = np.radians(beta)
    gamma = np.radians(gamma)
    ca = np.cos(alpha)
    cb = np.cos(beta)
    cg = np.cos(gamma)
    sg = np.sin(gamma)
    # a vector along x
    a_vec = [a, 0.0, 0.0]
    # b vector in xy-plane
    b_vec = [b * cg, b * sg, 0.0]
    # c vector with components
    cx = c * cb
    cy = c * (ca - cb * cg) / sg
    cz = c * np.sqrt(1.0 - cb**2 - ((ca - cb * cg) / sg) ** 2)
    c_vec = [cx, cy, cz]
    return np.array([a_vec, b_vec, c_vec])


class Crystal:
    def __init__(
        self, a, b, c, alpha, beta, gamma, spacegroup_number, atoms, symprec=1e-5
    ):
        """
        spacegroup_number: International Tables number (1-230).
        atoms: list of Atom objects (asymmetric unit).
        symprec: tolerance for symmetry detection.
        """
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

        # Get symmetry operations for this space group using a dummy atom
        self.rotations, self.translations = self._get_symmetry_operations()

        # Expand atoms to full unit cell
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
        """
        Use spglib to obtain all symmetry operations of the space group.
        A dummy cell with one atom at a general position ensures that
        no extra symmetry is accidentally added.
        """
        # Dummy atom at a general position (not on any special position)
        dummy_positions = [[0.1, 0.2, 0.3]]
        dummy_types = [1]  # any atomic number
        dummy_cell = (self._lattice_matrix, dummy_positions, dummy_types)
        # Get symmetry (space group will be the one we want, because the atom is general)
        sym = spglib.get_symmetry(dummy_cell, symprec=self.symprec)
        if sym is None:
            raise RuntimeError("spglib failed to get symmetry operations.")
        rotations = sym["rotations"]  # shape (n_ops, 3, 3)
        translations = sym["translations"]  # shape (n_ops, 3)
        return rotations, translations

    def _generate_full_atoms(self):
        """Apply all symmetry operations to the asymmetric unit atoms."""
        full = []
        # We'll use a set to avoid duplicates, but atoms are not hashable.
        # Instead, we keep a list and compare with a tolerance.
        eps = 1e-4
        for atom in self.atoms:
            for R, t in zip(self.rotations, self.translations):
                new_frac = R @ atom.frac + t
                new_frac = new_frac % 1.0
                # Check if this atom already exists (same element and near position)
                duplicate = False
                for existing in full:
                    if existing.element != atom.element:
                        continue
                    if np.allclose(existing.frac, new_frac, atol=eps):
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
        """Create a shallow copy for refinement (atoms are not deep-copied, but that's OK)."""
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
