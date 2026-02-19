import numpy as np

from ..atom.atom import Atom


class Crystal:
    def __init__(self, a, b, c, alpha, beta, gamma, space_group, atoms):
        self.a = a
        self.b = b
        self.c = c
        self.alpha = np.radians(alpha)
        self.beta = np.radians(beta)
        self.gamma = np.radians(gamma)
        self.space_group = space_group
        self.atoms = atoms  # asymmetric unit

        self._compute_metrics()
        self.full_atoms = self._generate_full_atoms()

    def _compute_metrics(self):
        ca = np.cos(self.alpha)
        cb = np.cos(self.beta)
        cg = np.cos(self.gamma)
        sg = np.sin(self.gamma)
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

    def _generate_full_atoms(self):
        full = []
        for atom in self.atoms:
            positions = self.space_group.apply(atom.frac)
            for pos in positions:
                new_atom = Atom(
                    atom.element, pos[0], pos[1], pos[2], atom.occ, atom.Biso
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
        """Create a shallow copy (atoms are not deep-copied, but that's OK for refinement)."""
        new_crystal = Crystal(
            self.a,
            self.b,
            self.c,
            np.degrees(self.alpha),
            np.degrees(self.beta),
            np.degrees(self.gamma),
            self.space_group,
            self.atoms,
        )
        # Ensure the copy recalculates everything
        new_crystal._compute_metrics()
        new_crystal.full_atoms = new_crystal._generate_full_atoms()
        return new_crystal
