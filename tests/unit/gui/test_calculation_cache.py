"""Кэш отражений: ключ атомов через Atom.frac / Atom.Biso."""

from src.gui.calculation import CalculationMixin
from src.model.atom.atom import Atom


def test_atoms_cache_tuple_uses_atom_frac_and_biso():
    atoms = [Atom("Na", 0.1, 0.2, 0.3, 0.9, 1.5)]
    key = CalculationMixin._atoms_cache_tuple(atoms)
    assert key == (("Na", 0.1, 0.2, 0.3, 0.9, 1.5),)
