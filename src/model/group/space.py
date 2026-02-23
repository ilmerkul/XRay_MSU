import numpy as np


# ----------------------------------------------------------------------
# 2. Space group handling (simplified – generators only)
# ----------------------------------------------------------------------
class SpaceGroup:
    def __init__(self, generators):
        """
        generators: list of tuples (R, t) where R is 3x3 integer matrix,
                    t is 3-element translation vector (fractional).
        """
        self.generators = generators
        self.operations = self._generate_operations()

    def _generate_operations(self):
        """Generate all symmetry operations by combining generators."""

        # We'll store operations as (R, t) where R is a tuple of tuples (hashable)
        # and t is a tuple of floats rounded to avoid floating point issues.
        def make_hashable(R, t):
            R_tuple = tuple(tuple(row) for row in R)
            t_tuple = tuple(np.round(t, decimals=10))  # round to avoid tiny differences
            return (R_tuple, t_tuple)

        # Start with identity
        I = np.eye(3, dtype=int)
        t0 = np.zeros(3)
        identity = make_hashable(I, t0)

        ops_set = {identity}
        ops_list = [identity]

        # Use a list as a queue for new operations
        new_ops = [identity]
        while new_ops:
            R1_hash, t1_hash = new_ops.pop()
            # Convert back to numpy for multiplication
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

        # Convert back to numpy arrays for later use
        self.operations = [(np.array(R), np.array(t)) for R, t in ops_list]
        return self.operations

    def apply(self, x):
        """Apply all operations to a fractional coordinate x (3-element array)."""
        positions = []
        for R, t in self.operations:
            x_new = R @ x + t
            positions.append(x_new % 1.0)
        return positions


def multiplicity(crystal, hkl):
    """
    Compute reflection multiplicity using the point-group operations
    (rotational parts of the space group). Ignores translations.
    """
    hkl = np.array(hkl, dtype=float)
    orbits = set()
    for R in crystal.rotations:
        # Real-space rotation R acts on reciprocal vector as R^T (since R is orthogonal)
        hkl_rot = R.T @ hkl
        # Round to integer (within tolerance)
        hkl_rounded = tuple(int(round(x)) for x in hkl_rot)
        orbits.add(hkl_rounded)
    return len(orbits)
