from pathlib import Path

import pytest

from src.model.atom.atom import AtomicScatteringFactor
from src.runtime_layout import ASF_MIN_BYTES, asf_data_path


class TestAtomicScatteringFactor:
    def test_cu_lookup(self, asf: AtomicScatteringFactor):
        f0 = asf.get_f0("Cu", 0.1)
        assert f0 > 0

    def test_cu_case_insensitive(self, asf: AtomicScatteringFactor):
        assert asf.get_f0("cu", 0.1) == asf.get_f0("Cu", 0.1)

    def test_normalize_element_symbol(self):
        assert AtomicScatteringFactor.normalize_element_symbol(" cu ") == "Cu"
        assert AtomicScatteringFactor.normalize_element_symbol("NA") == "Na"
        assert AtomicScatteringFactor.normalize_element_symbol("Cu2+") == "Cu2+"

    def test_unknown_symbol_raises(self, asf: AtomicScatteringFactor):
        with pytest.raises(ValueError, match="XyZz"):
            asf.get_f0("XyZz", 0.0)

    def test_empty_file_raises(self, tmp_path):
        bad = tmp_path / "empty.dat"
        bad.write_text("# header only\n", encoding="utf-8")
        with pytest.raises(ValueError, match="пуст или не распознан"):
            AtomicScatteringFactor(str(bad))


class TestAsfDataPath:
    def test_resolves_repo_file(self, repo_root):
        path = asf_data_path()
        expected = (repo_root / "data" / "f0_WaasKirf.dat").resolve()
        assert Path(path) == expected

    def test_repo_file_large_enough(self, repo_root):
        dat = repo_root / "data" / "f0_WaasKirf.dat"
        assert dat.stat().st_size >= ASF_MIN_BYTES
