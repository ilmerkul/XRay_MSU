import numpy as np


class SpaceGroup:
    def __init__(self, generators):
        self.generators = generators
        self.operations = self._generate_operations()

    def _generate_operations(self):
        def make_hashable(R, t):
            R_tuple = tuple(tuple(row) for row in R)
            t_tuple = tuple(np.round(t, decimals=10))
            return (R_tuple, t_tuple)

        I = np.eye(3, dtype=int)
        t0 = np.zeros(3)
        identity = make_hashable(I, t0)

        ops_set = {identity}
        ops_list = [identity]

        new_ops = [identity]
        while new_ops:
            R1_hash, t1_hash = new_ops.pop()

            R1 = np.array(R1_hash)
            t1 = np.array(t1_hash)
            for Rg, tg in self.generators:
                R_new = Rg @ R1
                t_new = (Rg @ t1 + tg) % 1.0
                new_hash = make_hashable(R_new, t_new)
                if new_hash not in ops_set:
                    ops_set.add(new_hash)
                    ops_list.append(new_hash)
                    new_ops.append(new_hash)

        self.operations = [(np.array(R), np.array(t)) for R, t in ops_list]
        return self.operations

    def apply(self, x):
        positions = []
        for R, t in self.operations:
            x_new = R @ x + t
            positions.append(x_new % 1.0)
        return positions


def multiplicity(crystal, hkl):
    hkl = np.array(hkl, dtype=float)
    orbits = set()
    for R in crystal.rotations:
        R_inv = np.round(np.linalg.inv(R)).astype(int)
        hkl_rot = R_inv.T @ hkl
        hkl_rounded = tuple(int(round(x)) for x in hkl_rot)
        orbits.add(hkl_rounded)
    print(orbits, hkl)
    return len(orbits)