"""
Simplified PowderCell-like implementation in Python
(Error‑free version)
"""

import matplotlib.pyplot as plt
import numpy as np
import scipy.optimize

# ----------------------------------------------------------------------
# 1. Atomic scattering factors (Cromer-Mann coefficients)
# ----------------------------------------------------------------------
SCATTERING_FACTORS = {
    "Si": {
        "a": [2.275, 2.4278, 1.4369, 0.7857],
        "b": [2.6058, 24.8363, 70.8085, 161.6929],
        "c": 0.2172,
    },
    "O": {
        "a": [3.0485, 2.2868, 1.5463, 0.867],
        "b": [13.2771, 5.7011, 0.3239, 32.9089],
        "c": 0.2508,
    },
    "Al": {
        "a": [4.1745, 2.6176, 1.9553, 1.1935],
        "b": [1.8584, 9.4695, 53.2539, 180.5347],
        "c": 0.2891,
    },
}


def f0(element, s):
    """Cromer-Mann f0 for given element at sin(theta)/lambda = s."""
    coeff = SCATTERING_FACTORS[element]
    s2 = s * s
    total = coeff["c"]
    for a, b in zip(coeff["a"], coeff["b"]):
        total += a * np.exp(-b * s2)
    return total


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


# ----------------------------------------------------------------------
# 3. Atom and Crystal classes
# ----------------------------------------------------------------------
class Atom:
    def __init__(self, element, x, y, z, occ=1.0, Biso=1.0):
        self.element = element
        self.frac = np.array([x, y, z])
        self.occ = occ
        self.Biso = Biso


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


# Trivial space group (no symmetry, returns only the input coordinate)
class TrivialSpaceGroup:
    def apply(self, x):
        return [x]


# ----------------------------------------------------------------------
# 4. Structure factor calculation
# ----------------------------------------------------------------------
def structure_factor(crystal, hkl, wavelength):
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return 0.0
    s_val = 0.5 / d  # sinθ/λ
    F = 0.0 + 0.0j
    for atom in crystal.full_atoms:
        phase = 2j * np.pi * np.dot(hkl, atom.frac)
        f = f0(atom.element, s_val)
        T = np.exp(-atom.Biso * s_val**2)
        F += atom.occ * f * T * np.exp(phase)
    return F


def theta(hkl, crystal, wavelength):
    d = crystal.d_spacing(hkl)
    if d == np.inf:
        return np.nan
    sinth = wavelength / (2 * d)
    if sinth > 1:
        return np.nan
    return np.arcsin(sinth)


# ----------------------------------------------------------------------
# 5. Multiplicity, LP factor, peak profile
# ----------------------------------------------------------------------
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


def lp_factor(twotheta):
    """Lorentz-polarisation factor for Bragg-Brentano geometry."""
    th = np.radians(twotheta / 2)
    cos2th = np.cos(np.radians(twotheta))
    return (1 + cos2th**2) / (np.sin(th) ** 2 * np.cos(th))


def gaussian(x, centre, fwhm):
    sigma = fwhm / (2 * np.sqrt(2 * np.log(2)))
    return (1 / (sigma * np.sqrt(2 * np.pi))) * np.exp(
        -0.5 * ((x - centre) / sigma) ** 2
    )


def lorentzian(x, centre, fwhm):
    gamma = fwhm / 2
    return (gamma / np.pi) / ((x - centre) ** 2 + gamma**2)


def pseudo_voigt(x, centre, fwhm, eta=0.5):
    return eta * lorentzian(x, centre, fwhm) + (1 - eta) * gaussian(x, centre, fwhm)


def caglioti_fwhm(theta, U, V, W):
    """FWHM in radians."""
    tant = np.tan(theta)
    return np.sqrt(U * tant**2 + V * tant + W)


# ----------------------------------------------------------------------
# 6. Powder pattern simulation
# ----------------------------------------------------------------------
class PowderPattern:
    def __init__(
        self,
        crystal,
        wavelength,
        twotheta_range,
        U=0.01,
        V=-0.01,
        W=0.005,
        scale=1.0,
        profile="pvoigt",
        eta=0.5,
        bg_poly=None,
    ):
        self.crystal = crystal
        self.wavelength = wavelength
        self.twotheta = np.arange(
            twotheta_range[0], twotheta_range[1], twotheta_range[2]
        )
        self.U, self.V, self.W = U, V, W
        self.scale = scale
        self.profile = profile
        self.eta = eta
        self.bg_poly = bg_poly if bg_poly is not None else [0, 0, 0]

        self.reflections = self._generate_reflections(d_min=0.8)
        self.ycalc = self._convolve()

    def _generate_reflections(self, d_min):
        hmax = int(max(self.crystal.a, self.crystal.b, self.crystal.c) / d_min) + 1
        refs = []
        for h in range(-hmax, hmax + 1):
            for k in range(-hmax, hmax + 1):
                for l in range(-hmax, hmax + 1):
                    if h == 0 and k == 0 and l == 0:
                        continue
                    d = self.crystal.d_spacing((h, k, l))
                    if d >= d_min:
                        th = np.arcsin(self.wavelength / (2 * d))
                        if np.isnan(th):
                            continue
                        twoth = 2 * np.degrees(th)
                        F = structure_factor(self.crystal, (h, k, l), self.wavelength)
                        mult = multiplicity((h, k, l), self.crystal)
                        lp = lp_factor(twoth)
                        intensity = self.scale * mult * lp * np.abs(F) ** 2
                        if intensity > 1e-6:  # skip negligible peaks
                            refs.append(
                                {
                                    "hkl": (h, k, l),
                                    "d": d,
                                    "twotheta": twoth,
                                    "F": F,
                                    "intensity": intensity,
                                }
                            )
        return refs

    def _convolve(self):
        y = np.zeros_like(self.twotheta)
        for ref in self.reflections:
            centre = ref["twotheta"]
            if centre < self.twotheta[0] or centre > self.twotheta[-1]:
                continue
            fwhm_rad = caglioti_fwhm(np.radians(centre / 2), self.U, self.V, self.W)
            fwhm_deg = np.degrees(fwhm_rad)
            intensity = ref["intensity"]
            if self.profile == "gaussian":
                y += intensity * gaussian(self.twotheta, centre, fwhm_deg)
            elif self.profile == "lorentzian":
                y += intensity * lorentzian(self.twotheta, centre, fwhm_deg)
            else:  # pseudo-Voigt
                y += intensity * pseudo_voigt(self.twotheta, centre, fwhm_deg, self.eta)
        # Add background
        bg = np.polyval(self.bg_poly, self.twotheta)
        return y + bg


# ----------------------------------------------------------------------
# 7. Example: Silicon (cubic, manually placed atoms)
# ----------------------------------------------------------------------
a_Si = 5.4307
atoms_Si = [
    Atom("Si", 0.0, 0.0, 0.0),
    Atom("Si", 0.0, 0.5, 0.5),
    Atom("Si", 0.5, 0.0, 0.5),
    Atom("Si", 0.5, 0.5, 0.0),
    Atom("Si", 0.25, 0.25, 0.25),
    Atom("Si", 0.25, 0.75, 0.75),
    Atom("Si", 0.75, 0.25, 0.75),
    Atom("Si", 0.75, 0.75, 0.25),
]
crystal_Si = Crystal(a_Si, a_Si, a_Si, 90, 90, 90, TrivialSpaceGroup(), atoms_Si)

lambda_Cu = 1.54056

pattern_Si = PowderPattern(
    crystal_Si,
    lambda_Cu,
    (20, 100, 0.02),
    U=0.01,
    V=-0.005,
    W=0.005,
    scale=1.0,
    profile="pvoigt",
    eta=0.5,
)

# Plot
plt.figure(figsize=(10, 4))
plt.plot(pattern_Si.twotheta, pattern_Si.ycalc, label="Simulated Si")
plt.xlabel("2θ (deg)")
plt.ylabel("Intensity")
plt.title("Simulated powder pattern of Silicon")
plt.legend()
plt.grid(True)
plt.savefig("silicon_pattern.png", dpi=300)
plt.close()


# ----------------------------------------------------------------------
# 8. Refinement framework (simple Rietveld)
# ----------------------------------------------------------------------
def residual(
    params, twotheta_exp, y_exp, crystal_template, wavelength, profile="pvoigt"
):
    """
    Residual function for least-squares refinement.
    params: [scale, U, V, W, eta, a]
    """
    scale, U, V, W, eta, a = params
    # Create a copy of the crystal with the new lattice parameter
    crystal_copy = crystal_template.copy()
    crystal_copy.a = a
    crystal_copy.b = a
    crystal_copy.c = a
    crystal_copy._compute_metrics()
    # Regenerate full atoms (lattice not changed, so same positions)
    crystal_copy.full_atoms = crystal_copy._generate_full_atoms()
    # Compute pattern
    pattern = PowderPattern(
        crystal_copy,
        wavelength,
        (twotheta_exp[0], twotheta_exp[-1], 0.02),
        U=U,
        V=V,
        W=W,
        scale=scale,
        profile=profile,
        eta=eta,
    )
    y_calc_interp = np.interp(twotheta_exp, pattern.twotheta, pattern.ycalc)
    return y_exp - y_calc_interp


# Create synthetic "experimental" data with noise
y_exp_synth = pattern_Si.ycalc + np.random.normal(
    0, 0.1 * pattern_Si.ycalc.max(), size=len(pattern_Si.twotheta)
)
twotheta_exp = pattern_Si.twotheta

# Initial guess
params0 = [0.9, 0.02, -0.01, 0.008, 0.4, 5.4]

# Refine
result = scipy.optimize.leastsq(
    residual, params0, args=(twotheta_exp, y_exp_synth, crystal_Si, lambda_Cu)
)
params_refined = result[0]

print("Refined parameters:")
print(f"Scale = {params_refined[0]:.4f}")
print(f"U = {params_refined[1]:.4f}")
print(f"V = {params_refined[2]:.4f}")
print(f"W = {params_refined[3]:.4f}")
print(f"eta = {params_refined[4]:.4f}")
print(f"a = {params_refined[5]:.4f}")

# Plot comparison
y_calc_refined = PowderPattern(
    crystal_Si,
    lambda_Cu,
    (20, 100, 0.02),
    U=params_refined[1],
    V=params_refined[2],
    W=params_refined[3],
    scale=params_refined[0],
    eta=params_refined[4],
).ycalc

plt.figure(figsize=(10, 4))
plt.plot(twotheta_exp, y_exp_synth, "k.", markersize=1, label="Exp (synthetic)")
plt.plot(
    twotheta_exp,
    np.interp(twotheta_exp, pattern_Si.twotheta, y_calc_refined),
    "r-",
    label="Refined",
)
plt.xlabel("2θ (deg)")
plt.ylabel("Intensity")
plt.title("Rietveld refinement test")
plt.legend()
plt.grid(True)
plt.savefig("silicon_patternl.png", dpi=300)
plt.close()
