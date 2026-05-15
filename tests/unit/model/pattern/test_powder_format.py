import pytest

from src.model.pattern.powder import _format_F_tsv


class TestFormatFTsv:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (0.0, "0"),
            (1e-12, "0"),
            (1.5, "1.500"),
            (2j, "2.000j"),
            (1 + 2j, "1.000+2.000j"),
            (-0.5 - 0.25j, "-0.500-0.250j"),
        ],
    )
    def test_format(self, value: complex, expected: str):
        assert _format_F_tsv(value) == expected
