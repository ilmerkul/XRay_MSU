from typing import List, Tuple

import matplotlib.pyplot as plt
import numpy as np

from ..atom.atom import Atom, AtomicScatteringFactor
from ..group.space import SpaceGroup
from .utils import canonical_frac, frac_periodic_allclose

default_colors = {
    "H": "white",
    "C": "#505050",
    "N": "#3050F8",
    "O": "#FF0D0D",
    "F": "#90E050",
    "Cl": "#1FF01F",
    "Br": "#A62929",
    "I": "#940094",
    "He": "#D9FFFF",
    "Ne": "#030404",
    "Ar": "#80C1E9",
    "Kr": "#5CB8D1",
    "Xe": "#429EB0",
    "P": "#FF8000",
    "S": "#FFFF30",
    "B": "#FFB5B5",
    "Li": "#B22222",
    "Na": "#AB5CF2",
    "Mg": "#8AFF00",
    "Al": "#BFA6A6",
    "Si": "#F0C8A0",
    "K": "#8F40D4",
    "Ca": "#3DFF00",
    "Sc": "#E6E6E6",
    "Ti": "#BFC2C7",
    "Cr": "#8A99C7",
    "Mn": "#9C7AC7",
    "Fe": "#E06633",
    "Co": "#F090A0",
    "Ni": "#50D050",
    "Cu": "#C88033",
    "Zn": "#7D80B0",
    "Ga": "#C28F8F",
    "Ge": "#668F8F",
    "As": "#BD80E3",
    "Se": "#FFA100",
    "Rb": "#702EB0",
    "Sr": "#00FF00",
    "Y": "#94FFFF",
    "Zr": "#94E0E0",
    "Nb": "#73C2C2",
    "Mo": "#54B5B5",
    "Tc": "#3B9E9E",
    "Ru": "#248F8F",
    "Rh": "#0A7D8C",
    "Pd": "#006985",
    "Ag": "#C0C0C0",
    "Cd": "#FFD98F",
    "In": "#A67573",
    "Sn": "#668080",
    "Sb": "#9E63B5",
    "Te": "#D47A4D",
    "Cs": "#57178F",
    "Ba": "#00A900",
    "La": "#70D4D4",
    "Ce": "#FFFFC7",
    "Pr": "#D9FFC7",
    "Nd": "#C7FFC7",
    "Pm": "#A3FFC7",
    "Sm": "#8FFFC7",
    "Eu": "#61FFC7",
    "Gd": "#45FFC7",
    "Tb": "#30FFC7",
    "Dy": "#1FFFC7",
    "Ho": "#00FF9C",
    "Er": "#00E675",
    "Tm": "#00D452",
    "Yb": "#00BF38",
    "Lu": "#00AB24",
    "Hf": "#4DC2FF",
    "Ta": "#4DA6FF",
    "W": "#4D94FF",
    "Re": "#267DFF",
    "Os": "#2666FF",
    "Ir": "#175CFF",
    "Pt": "#D0D0E0",
    "Au": "#FFD123",
    "Hg": "#B8B8D0",
    "Tl": "#A6544D",
    "Pb": "#575961",
    "Bi": "#9E4FB5",
    "Po": "#CC5C99",
    "At": "#754F45",
    "Rn": "#428296",
    "Fr": "#420066",
    "Ra": "#007D00",
    "Ac": "#70ABAB",
    "Th": "#00BAFF",
    "Pa": "#00A1FF",
    "U": "#008FFF",
    "Np": "#0080FF",
    "Pu": "#006BFF",
    "Am": "#545CF2",
    "Cm": "#785CE3",
    "Bk": "#8A4FE3",
    "Cf": "#A136D4",
    "Es": "#B31FD4",
    "Fm": "#B31FBA",
    "Md": "#B30DA6",
    "No": "#BD0D87",
    "Lr": "#C70066",
    "Rf": "#CC0059",
    "Db": "#D1004F",
    "Sg": "#D90045",
    "Bh": "#E00038",
    "Hs": "#E6002E",
    "Mt": "#EB0026",
}


class Crystal:
    def __init__(
        self,
        a: float,
        b: float,
        c: float,
        alpha: float,
        beta: float,
        gamma: float,
        asf: AtomicScatteringFactor,
        spacegroup_number: int = None,
        atoms: List[Atom] = None,
        symprec: float = 1e-5,
        spacegroup: SpaceGroup = None,
    ):
        self.asf = asf

        self.a = a
        self.b = b
        self.c = c
        self.alpha = np.radians(alpha)
        self.beta = np.radians(beta)
        self.gamma = np.radians(gamma)
        self.atoms = atoms if atoms is not None else []
        self.symprec = symprec

        self._compute_metrics()
        self._lattice_matrix = Crystal.lattice_to_matrix(a, b, c, alpha, beta, gamma)

        if spacegroup is not None:
            self.spacegroup = spacegroup
        elif spacegroup_number is not None:
            self.spacegroup = SpaceGroup.from_spacegroup_number(
                number=spacegroup_number
            )
        elif len(atoms) != 0:
            self.spacegroup = SpaceGroup.from_structure(
                lattice=self._lattice_matrix, atoms=atoms, symprec=symprec
            )
        else:
            raise ValueError("Either spacegroup or spacegroup_number must be provided.")

        self.rotations = self.spacegroup.rotations
        self.translations = self.spacegroup.translations

        self.full_atoms = self._generate_full_atoms()

    @staticmethod
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

    def _generate_full_atoms(self, symprec: float = 1e-5) -> List[Atom]:
        full_atoms = []

        for atom in self.atoms:
            # Только кристаллографические операции (не lattice_operations):
            # иначе дублируются эквивалентные точки и ломается F(hkl).
            for R, t in self.spacegroup.operations:
                pos = np.asarray(R, dtype=float) @ np.asarray(
                    atom.frac, dtype=float
                ) + np.asarray(t, dtype=float)
                new_frac = canonical_frac(pos, symprec)

                duplicate = False
                for existing in full_atoms:
                    if existing.element == atom.element and frac_periodic_allclose(
                        new_frac, existing.frac, atol=symprec
                    ):
                        duplicate = True
                        break

                if not duplicate:
                    new_atom = Atom(
                        element=atom.element,
                        x=float(new_frac[0]),
                        y=float(new_frac[1]),
                        z=float(new_frac[2]),
                        occ=atom.occ,
                        Biso=atom.Biso,
                    )
                    full_atoms.append(new_atom)

        full_atoms.sort(key=lambda a: (a.element, *a.frac))
        return full_atoms

    def d_spacing(self, hkl):
        h = np.array(hkl, dtype=float)
        invd2 = np.dot(h, np.dot(self.Gstar, h))
        if invd2 <= 0:
            return np.inf
        return 1.0 / np.sqrt(invd2)

    def copy(self):
        atoms_copy = [atom.copy() for atom in self.atoms]
        spacegroup_copy = SpaceGroup(self.spacegroup.generators)
        return Crystal(
            self.a,
            self.b,
            self.c,
            np.degrees(self.alpha),
            np.degrees(self.beta),
            np.degrees(self.gamma),
            atoms=atoms_copy,
            symprec=self.symprec,
            spacegroup=spacegroup_copy,
        )

    @staticmethod
    def hkl2tuple(hkl):
        return tuple(int(round(x)) for x in hkl)

    def multiplicity(self, hkl):
        hkl = np.array(hkl, dtype=float)
        orbits = set()
        for R in self.rotations:
            R_inv = np.round(np.linalg.inv(R)).astype(int)
            hkl_rot = R_inv.T @ hkl
            hkl_rounded = Crystal.hkl2tuple(hkl_rot)
            orbits.add(hkl_rounded)
        return len(orbits), orbits

    def invd2_hkl(self, hkl):
        """1/d² = hᵀ G* h для целочисленных (или вещественных) Миллера."""
        h = np.array(hkl, dtype=float)
        return float(np.dot(h, np.dot(self.Gstar, h)))

    def multiplicity_metric(
        self, hkl, max_index: int, rtol: float = 1e-7, atol: float = 1e-12
    ):
        """
        Кратность и «орбита» через перебор: все целые (h',k',l') в кубе
        [-max_index, max_index]³ с тем же 1/d² (в пределах rtol/atol), кроме (0,0,0).

        Не совпадает с кристаллографической кратностью, если на одной сфере в
        обратном пространстве лежат отражения с разными |F| (случайные вырождения).
        """
        target = self.invd2_hkl(hkl)
        if target <= 0:
            return 1, {Crystal.hkl2tuple(hkl)}
        scale = max(target, 1.0)
        orbits = set()
        for hp in range(-max_index, max_index + 1):
            for kp in range(-max_index, max_index + 1):
                for lp in range(-max_index, max_index + 1):
                    if hp == 0 and kp == 0 and lp == 0:
                        continue
                    m = self.invd2_hkl((hp, kp, lp))
                    if m <= 0:
                        continue
                    if np.isclose(m, target, rtol=rtol, atol=atol * scale):
                        orbits.add(Crystal.hkl2tuple((hp, kp, lp)))
        if not orbits:
            return 1, {Crystal.hkl2tuple(hkl)}
        return len(orbits), orbits

    def save_image(
        self,
        filename,
        view=(30, 30),
        element_colors=None,
        atom_scale=1.0,
        show_cell=True,
        dpi=100,
        show_labels=True,
    ):
        if element_colors is not None:
            default_colors.update(element_colors)
        colors = default_colors

        fig = plt.figure(figsize=(8, 8))
        ax = fig.add_subplot(111, projection="3d")

        lattice = self._lattice_matrix
        full_atoms = self._generate_full_atoms()
        for atom in full_atoms:
            cart = np.dot(atom.frac, lattice)
            color = colors.get(atom.element, "gray")
            ax.scatter(
                cart[0],
                cart[1],
                cart[2],
                c=color,
                s=50 * atom_scale,
                edgecolors="black",
                linewidth=0.5,
            )

            if show_labels:
                label = f"({atom.frac[0]:.2f}, {atom.frac[1]:.2f}, {atom.frac[2]:.2f})"
                ax.text(
                    cart[0], cart[1], cart[2], label, ha="left", va="bottom", fontsize=6
                )

        if show_cell:
            o = np.zeros(3)
            a, b, c = lattice
            corners = [o, a, b, c, a + b, a + c, b + c, a + b + c]
            edges = [
                (0, 1),
                (0, 2),
                (0, 3),
                (1, 4),
                (1, 5),
                (2, 4),
                (2, 6),
                (3, 5),
                (3, 6),
                (4, 7),
                (5, 7),
                (6, 7),
            ]
            for i, j in edges:
                ax.plot(
                    [corners[i][0], corners[j][0]],
                    [corners[i][1], corners[j][1]],
                    [corners[i][2], corners[j][2]],
                    color="black",
                    linewidth=1,
                )

        ax.view_init(elev=view[0], azim=view[1])
        ax.set_xlabel("x (Å)")
        ax.set_ylabel("y (Å)")
        ax.set_zlabel("z (Å)")
        ax.set_title("Crystal structure")

        plt.legend()
        plt.savefig(filename, dpi=dpi, bbox_inches="tight")
        plt.close(fig)
        print(f"Изображение сохранено в {filename}")
