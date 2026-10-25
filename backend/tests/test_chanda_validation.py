"""validate_pattern: how far a line's laghu-guru pattern is from one meter's pattern."""

INDRAVAJRA = "इन्द्रवज्रा"
INDRAVAJRA_LG = "GGLGGLLGLGG"


def test_an_exact_pattern_is_valid(chanda):
    result = chanda.validate_pattern(INDRAVAJRA_LG, INDRAVAJRA)
    assert result == {
        "is_valid": True,
        "expected_pattern": INDRAVAJRA_LG,
        "actual_pattern": INDRAVAJRA_LG,
        "match_percentage": 100.0,
        "mismatches": [],
    }


def test_a_light_final_syllable_is_tolerated(chanda):
    """The last syllable of a pada may be light where the meter has it heavy."""
    result = chanda.validate_pattern("GGLGGLLGLGL", INDRAVAJRA)
    assert result["is_valid"] is True
    assert result["mismatches"] == [(11, "G", "L")]


def test_a_wrong_length_line_is_invalid_and_says_why(chanda):
    result = chanda.validate_pattern("GLGGGLGG", INDRAVAJRA)
    assert result["is_valid"] is False
    assert ("length", 11, 8) in result["mismatches"]
    assert result["match_percentage"] == 45.5


def test_an_unknown_meter_cannot_be_judged(chanda):
    result = chanda.validate_pattern("GGL", "nonexistent")
    assert (result["is_valid"], result["expected_pattern"]) == (None, None)


def test_tolerance_and_anta_guru_helpers(chanda):
    assert chanda.pattern_matches_with_tolerance("GGLG", "GGLL")
    assert not chanda.pattern_matches_with_tolerance("GGLG", "LLGL")
    assert not chanda.pattern_matches_with_tolerance("GG", "GGG")
    assert chanda.should_be_guru("स", is_last=True)
    assert not chanda.should_be_guru("स")
