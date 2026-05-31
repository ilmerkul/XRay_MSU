import pytest

from src.model.crystal.crystal import Crystal


@pytest.mark.parametrize(
    "hkl",
    [(1, 0, 0), (1, 1, 0), (2, 1, 0), (1, 1, 1), (3, 2, 1)],
)
def test_build_metric_orbit_map_matches_multiplicity_metric(
    nacl_crystal: Crystal, hkl: tuple[int, int, int]
):
    max_index = 8
    rtol, atol = 1e-7, 1e-12
    orbit_map = nacl_crystal.build_metric_orbit_map(max_index, rtol=rtol, atol=atol)
    mult_direct, group_direct = nacl_crystal.multiplicity_metric(
        hkl, max_index, rtol=rtol, atol=atol
    )
    hkl_t = Crystal.hkl2tuple(hkl)
    assert hkl_t in orbit_map
    mult_map, group_map = orbit_map[hkl_t]
    assert mult_map == mult_direct
    assert group_map == frozenset(group_direct)
