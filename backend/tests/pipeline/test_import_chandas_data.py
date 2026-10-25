"""The sanskrit-coders importer must write gaṇa strings the engine can read."""

import pytest

from backend.pipeline.meter_tables import GANA_PATTERNS, expand_gana
from backend.scripts.import_chandas_data import calculate_matra, calculate_syllables, convert_to_gana_notation


@pytest.mark.parametrize(
    ("pattern", "gana"),
    [
        ("LGGLGGLGGLGG", "यययय"),
        ("GGLGGLLGLGG", "ततजगग"),
        ("LLLLLLGGGLGGLGG", "ननमयय"),
        ("LGGLG", "यलग"),
        ("GGLGGLGGLGGGLLGLLLLG", "तततमसनलग"),
    ],
)
def test_gana_notation_uses_only_symbols_the_engine_reads(pattern, gana):
    converted = convert_to_gana_notation(pattern)
    assert converted == gana
    assert set(converted) <= set(GANA_PATTERNS)
    assert expand_gana(converted) == pattern.replace("L", "ल").replace("G", "ग")


def test_non_laghu_guru_patterns_have_no_gana():
    assert convert_to_gana_notation("LGX") == ""
    assert convert_to_gana_notation("") == ""


def test_syllable_and_matra_counts():
    assert calculate_syllables("LGGLG") == 5
    assert calculate_matra("LGGLG") == 8
    assert calculate_syllables("lgg") == 0
