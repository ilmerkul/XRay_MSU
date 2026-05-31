from typing import List

import matplotlib.pyplot as plt
import numpy as np

from ..atom.atom import Atom, AtomicScatteringFactor
from ..atom.const import default_colors
from ..group.space import SpaceGroup
from .utils import canonical_frac, frac_periodic_allclose


class Crystal:
    """Кристаллическая структура: решётка, атомы и пространственная группа."""

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
        """Создаёт кристалл и разворачивает атомы по симметрии.

        Args:
            a: Параметр решётки a (Å).
            b: Параметр решётки b (Å).
            c: Параметр решётки c (Å).
            alpha: Угол α (градусы).
            beta: Угол β (градусы).
            gamma: Угол γ (градусы).
            asf: Таблица атомных факторов f₀.
            spacegroup_number: Номер пространственной группы (1–230).
            atoms: Атомы элементарной ячейки.
            symprec: Допуск для определения симметрии.
            spacegroup: Готовый объект ``SpaceGroup`` (альтернатива номеру).

        Raises:
            ValueError: Если не заданы ни ``spacegroup``, ни ``spacegroup_number``, ни атомы.
        """
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
        """Строит матрицу базисных векторов решётки в декартовых координатах.

        Args:
            a: Длина вектора a (Å).
            b: Длина вектора b (Å).
            c: Длина вектора c (Å).
            alpha: Угол между b и c (градусы).
            beta: Угол между a и c (градусы).
            gamma: Угол между a и b (градусы).

        Returns:
            Массив 3×3: строки — векторы a, b, c.
        """
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
        """Вычисляет метрический тензор G, объём V и обратный тензор G*."""
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
        """Разворачивает атомы элементарной ячейки по операциям пространственной группы.

        Args:
            symprec: Допуск при сравнении эквивалентных позиций.

        Returns:
            Отсортированный список уникальных атомов ``full_atoms``.
        """
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
        """Вычисляет межплоскостное расстояние d для индексов (hkl).

        Args:
            hkl: Индексы Миллера.

        Returns:
            Расстояние d (Å) или ``inf``, если 1/d² ≤ 0.
        """
        h = np.array(hkl, dtype=float)
        invd2 = np.dot(h, np.dot(self.Gstar, h))
        if invd2 <= 0:
            return np.inf
        return 1.0 / np.sqrt(invd2)

    def copy(self):
        """Создаёт независимую копию кристалла с теми же параметрами.

        Returns:
            Новый объект ``Crystal``.
        """
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
        """Округляет индексы Миллера до целых и возвращает кортеж.

        Args:
            hkl: Индексы (h, k, l).

        Returns:
            Кортеж целых (h, k, l).
        """
        return tuple(int(round(x)) for x in hkl)

    def multiplicity(self, hkl):
        """Кратность отражения по симметрии обратной решётки.

        Args:
            hkl: Индексы Миллера.

        Returns:
            Кортеж ``(число эквивалентных hkl, множество эквивалентных индексов)``.
        """
        hkl = np.array(hkl, dtype=float)
        orbits = set()
        for R in self.rotations:
            R_inv = np.round(np.linalg.inv(R)).astype(int)
            hkl_rot = R_inv.T @ hkl
            hkl_rounded = Crystal.hkl2tuple(hkl_rot)
            orbits.add(hkl_rounded)
        return len(orbits), orbits

    def invd2_hkl(self, hkl):
        """Вычисляет 1/d² = hᵀ G* h для индексов Миллера.

        Args:
            hkl: Индексы (h, k, l).

        Returns:
            Значение 1/d² (Å⁻²).
        """
        h = np.array(hkl, dtype=float)
        return float(np.dot(h, np.dot(self.Gstar, h)))

    def _metric_hkl_invd2_cube(
        self, max_index: int
    ) -> tuple[list[tuple[int, int, int]], np.ndarray]:
        """Список hkl и 1/d² для всех ненулевых индексов в кубе перебора."""
        hkls: list[tuple[int, int, int]] = []
        invd2s: list[float] = []
        for hp in range(-max_index, max_index + 1):
            for kp in range(-max_index, max_index + 1):
                for lp in range(-max_index, max_index + 1):
                    if hp == 0 and kp == 0 and lp == 0:
                        continue
                    m = self.invd2_hkl((hp, kp, lp))
                    if m <= 0:
                        continue
                    hkls.append(Crystal.hkl2tuple((hp, kp, lp)))
                    invd2s.append(m)
        return hkls, np.asarray(invd2s, dtype=float)

    def build_metric_orbit_map(
        self,
        max_index: int,
        rtol: float = 1e-7,
        atol: float = 1e-12,
    ) -> dict[tuple[int, int, int], tuple[int, frozenset[tuple[int, int, int]]]]:
        """Предвычисляет метрические орбиты для всего куба индексов (один проход).

        Returns:
            Словарь ``hkl -> (кратность, frozenset орбиты)``.
        """
        hkls, invd2s = self._metric_hkl_invd2_cube(max_index)
        if not hkls:
            return {}

        orbit_map: dict[
            tuple[int, int, int], tuple[int, frozenset[tuple[int, int, int]]]
        ] = {}
        assigned: set[tuple[int, int, int]] = set()
        for seed, target in zip(hkls, invd2s, strict=True):
            if seed in assigned:
                continue
            scale = max(float(target), 1.0)
            mask = np.isclose(invd2s, target, rtol=rtol, atol=atol * scale)
            orbit = frozenset(hkls[i] for i in np.flatnonzero(mask))
            if not orbit:
                orbit = frozenset({seed})
            mult = len(orbit)
            for h in orbit:
                orbit_map[h] = (mult, orbit)
            assigned.update(orbit)
        return orbit_map

    def multiplicity_metric(
        self, hkl, max_index: int, rtol: float = 1e-7, atol: float = 1e-12
    ):
        """Кратность отражения по совпадению 1/d² (метрическая орбита).

        Перебирает целые (h', k', l') в кубе [-max_index, max_index]³ с тем же
        1/d² (в пределах rtol/atol). Может не совпадать с кристаллографической
        кратностью при вырожденных сферах в обратном пространстве.

        Args:
            hkl: Индексы Миллера.
            max_index: Полуразмер куба перебора индексов.
            rtol: Относительный допуск сравнения 1/d².
            atol: Абсолютный допуск (масштабируется по target).

        Returns:
            Кортеж ``(кратность, множество эквивалентных hkl)``.
        """
        target = self.invd2_hkl(hkl)
        if target <= 0:
            return 1, {Crystal.hkl2tuple(hkl)}
        hkls, invd2s = self._metric_hkl_invd2_cube(max_index)
        if not hkls:
            return 1, {Crystal.hkl2tuple(hkl)}
        scale = max(target, 1.0)
        mask = np.isclose(invd2s, target, rtol=rtol, atol=atol * scale)
        orbits = {hkls[i] for i in np.flatnonzero(mask)}
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
        """Сохраняет 3D-изображение структуры и элементарной ячейки в PNG.

        Args:
            filename: Путь к выходному файлу.
            view: Углы обзора (elev, azim) для 3D-осей.
            element_colors: Дополнительная палитра цветов элементов.
            atom_scale: Масштаб маркеров атомов.
            show_cell: Рисовать ли рёбра элементарной ячейки.
            dpi: Разрешение сохраняемого изображения.
            show_labels: Подписывать ли дробные координаты атомов.
        """
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
