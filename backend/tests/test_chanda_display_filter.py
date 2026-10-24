"""Confidence-based display filtering in Chanda.identify_line.

A meter lands in display_chanda_primary when its score is at least 80% of
the best score, and in the alternate list when it scores 7.0 or more.
"""

import re

import pytest

GITA_1_1_LINES = [
    "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
    "मामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय",
]

_SCORE = re.compile(r"\[(\d+\.\d)\]")


@pytest.mark.parametrize("line", GITA_1_1_LINES)
def test_anushtubh_half_verse_is_primary(chanda, line):
    result = chanda.identify_line(line)

    primary = result["display_chanda_primary"]
    assert "अनुष्टुभ्" in primary
    assert "(anuṣṭubh)" in primary
    assert result["confidence_scores"]["अनुष्टुभ्"] == (10.0, "exact_pattern")


@pytest.mark.parametrize("line", GITA_1_1_LINES)
def test_primary_scores_clear_the_threshold(chanda, line):
    result = chanda.identify_line(line)

    best = max(conf for conf, _ in result["confidence_scores"].values())
    shown = [float(s) for s in _SCORE.findall(result["display_chanda_primary"])]
    assert shown, "primary display should carry bracketed scores"
    assert all(score >= best * 0.8 for score in shown)


def test_counts_add_up(chanda):
    result = chanda.identify_line(GITA_1_1_LINES[0])

    primary_count = len(result["display_chanda_primary"].split(" | "))
    total = len(result["chanda"])
    assert primary_count + result["display_chanda_alternate_count"] <= total


def test_pada_ranges_survive_in_primary(chanda):
    result = chanda.identify_line(GITA_1_1_LINES[0])

    assert "पाद" in result["display_chanda"]
    assert "(पाद 1-2)" in result["display_chanda_primary"]
    assert "(पाद 3-4)" in result["display_chanda_primary"]


def test_short_fragment_matches_short_meters_only(chanda):
    # Four syllables (G G G G) match the four-syllable kanyā, not anuṣṭubh.
    result = chanda.identify_line("ध र्म क्षे त्रे")

    assert result["found"] is True
    assert "कन्या (kanyā) [10.0]" in result["display_chanda_primary"]
    assert "अनुष्टुभ्" not in result["display_chanda_primary"]
