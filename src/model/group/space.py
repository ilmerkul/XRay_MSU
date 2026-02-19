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


# Example space groups (not used in the Si example, but kept for illustration)
FD3M = SpaceGroup(
    [
        (np.array([[-1, 0, 0], [0, -1, 0], [0, 0, 1]], dtype=int), np.array([0, 0, 0])),
        (np.array([[-1, 0, 0], [0, 1, 0], [0, 0, -1]], dtype=int), np.array([0, 0, 0])),
        (
            np.array([[-1, 0, 0], [0, -1, 0], [0, 0, -1]], dtype=int),
            np.array([0, 0, 0]),
        ),
    ]
)


# Trivial space group (no symmetry, returns only the input coordinate)
class TrivialSpaceGroup:
    def apply(self, x):
        return [x]


def multiplicity(hkl, crystal):
    """
    Approximate multiplicity for cubic crystals.
    For non-cubic, a proper Laue-group generator would be needed.
    """
    h, k, l = hkl
    # Count permutations of |h|,|k|,|l| with signs (simple cubic Laue group m-3m)
    hkl_abs = np.sort([abs(h), abs(k), abs(l)])
    # For (000) we don't call this function
    if hkl_abs[2] == 0:
        # one index zero, two non-zero: e.g., (h,k,0)
        return (
            4 * 2
        )  # 4 permutations of two non-zero, 2 sign choices? Actually many cases.
        # For simplicity, return a placeholder.
    # We'll use a simple lookup for common cases:
    # For (111)-type: all equal non-zero -> 8
    if hkl_abs[0] == hkl_abs[1] == hkl_abs[2] and hkl_abs[2] > 0:
        return 8
    # For (h h 0) type: two equal, third zero -> 12
    if hkl_abs[0] == hkl_abs[1] and hkl_abs[2] == 0:
        return 12
    # For (h 0 0) type: one non-zero, others zero -> 6
    if hkl_abs[1] == 0:
        return 6
    # General (h k l) all different and non-zero -> 48
    return 48
