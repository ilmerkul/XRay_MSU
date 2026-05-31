"""Пространственные группы и симметрические операции (spglib)."""

from typing import List

import numpy as np
import spglib

from ..atom.atom import Atom
from ..atom.const import symbol_to_number


class SpaceGroup:
    """Пространственная группа, заданная генераторами (R, t)."""

    def __init__(self, generators):
        """Строит группу из списка генераторов симметрии.

        Args:
            generators: Список пар (матрица поворота, вектор трансляции).
        """
        self.generators = generators
        self.operations = self.generate_space_group(mod_lattice=False)
        self.lattice_operations = self.generate_space_group(mod_lattice=True)

    @staticmethod
    def from_spacegroup_number(number):
        """Создаёт группу по номеру пространственной группы (International Tables).

        Args:
            number: Номер пространственной группы (1–230).

        Returns:
            Объект ``SpaceGroup`` с операциями из базы spglib.
        """
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
        """Определяет симметрию структуры по решётке и атомам.

        Args:
            lattice: Матрица базисных векторов (3×3).
            atoms: Список атомов элементарной ячейки.
            symprec: Допуск для spglib при поиске симметрии.

        Returns:
            Объект ``SpaceGroup`` с операциями, найденными spglib.
        """
        positions = [atom.frac for atom in atoms]
        numbers = [symbol_to_number.get(atom.element, 0) for atom in atoms]

        cell = (lattice, positions, numbers)
        symmetry = spglib.get_symmetry(cell=cell, symprec=symprec)
        rotations = symmetry["rotations"]
        translations = symmetry["translations"]

        generators = list(zip(rotations, translations))
        return SpaceGroup(generators)

    def generate_space_group(self, mod_lattice=False, tol=1e-8, max_elements=512):
        """Замыкает множество генераторов до полной группы симметрии.

        Args:
            mod_lattice: Если ``True``, не приводить трансляции по mod 1 (решёточные операции).
            tol: Допуск округления при канонизации элементов.
            max_elements: Максимальное число элементов группы (защита от переполнения).

        Returns:
            Список пар (R, t) — все операции группы.
        """
        if not self.generators:
            dim = 3
        else:
            R0, _ = self.generators[0]
            dim = R0.shape[0]

        identity = np.eye(dim)
        zero = np.zeros(dim)

        def frac_part(t, mod_lattice=False):
            """Возвращает дробную часть трансляции.

            Args:
                t: Вектор трансляции.
                mod_lattice: Применять ли mod 1 к компонентам.

            Returns:
                Вектор трансляции (с mod 1 или без).
            """
            if not mod_lattice:
                return t - np.floor(t)
            return t

        def canonical(R, t):
            """Приводит операцию (R, t) к каноническому виду для сравнения.

            Args:
                R: Матрица поворота.
                t: Вектор трансляции.

            Returns:
                Хешируемый кортеж (R_tuple, t_tuple).
            """
            t_adj = frac_part(t, mod_lattice=mod_lattice)
            decimals = int(-np.log10(tol)) + 1
            R_rounded = np.round(R, decimals)
            t_rounded = np.round(t_adj, decimals)
            t_rounded = frac_part(t_rounded, mod_lattice=mod_lattice)
            R_tuple = tuple(tuple(row) for row in R_rounded)
            t_tuple = tuple(t_rounded)
            return (R_tuple, t_tuple)

        def compose(tr1, tr2):
            """Композиция двух операций симметрии.

            Args:
                tr1: Первая операция (R1, t1).
                tr2: Вторая операция (R2, t2).

            Returns:
                Составная операция (R1@R2, R1@t2 + t1).
            """
            R1, t1 = tr1
            R2, t2 = tr2
            R = R1 @ R2
            t = R1 @ t2 + t1
            t = frac_part(t, mod_lattice=mod_lattice)
            return (R, t)

        def inverse(tr):
            """Обратная операция симметрии.

            Args:
                tr: Операция (R, t).

            Returns:
                Обратная операция (R⁻¹, -R⁻¹@t).
            """
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
        """Матрицы поворота всех операций группы (без mod решётки).

        Returns:
            Список матриц 3×3.
        """
        return [R for R, t in self.operations]

    @property
    def translations(self):
        """Векторы трансляции всех операций группы (без mod решётки).

        Returns:
            Список векторов длины 3.
        """
        return [t for R, t in self.operations]

    def apply(self, x, mod_lattice=False):
        """Применяет все операции группы к точке x.

        Args:
            x: Координаты точки (дробные или декартовы).
            mod_lattice: Использовать ``lattice_operations`` вместо ``operations``.

        Returns:
            Список образов точки под каждой операцией.
        """
        ops = self.operations
        if mod_lattice:
            ops = self.lattice_operations
        positions = []
        for R, t in ops:
            x_new = R @ x + t
            positions.append(x_new)
        return positions
