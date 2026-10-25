"""Vedic-or-classical classification, its scoring helpers and the vocabulary tables it reads."""

import re

import pytest

from backend.core import text_classifier as tc
from backend.core import text_classifier_vocab as vocab

RV_1_1_1 = "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं"
GITA_1_1 = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय॥"
DEVANAGARI = re.compile(r"^[ऀ-ॿ᳐-᳿]+$")


@pytest.fixture(scope="module")
def classifier():
    return tc.TextClassifier()


class TestVocabulary:
    def test_classifier_exposes_the_vocab_tables(self):
        for name in (
            "VEDIC_VOCABULARY",
            "VEDIC_SUFFIXES",
            "VEDIC_PATTERNS",
            "VEDIC_SYLLABLE_COUNTS",
            "CLASSICAL_VOCABULARY",
            "CLASSICAL_STRUCTURAL_PATTERNS",
        ):
            assert getattr(tc.TextClassifier, name) is getattr(vocab, name)

    @pytest.mark.parametrize("words", [vocab.VEDIC_VOCABULARY, vocab.CLASSICAL_VOCABULARY, vocab.VEDIC_SUFFIXES])
    def test_word_lists_hold_devanagari_only(self, words):
        assert words
        assert [w for w in words if not DEVANAGARI.match(w)] == []

    @pytest.mark.parametrize("patterns", [vocab.VEDIC_PATTERNS, vocab.CLASSICAL_STRUCTURAL_PATTERNS])
    def test_patterns_compile(self, patterns):
        for pattern in patterns:
            re.compile(pattern)

    def test_vedic_syllable_counts_name_the_seven_major_meters(self):
        names = {meter for meter, _exact in vocab.VEDIC_SYLLABLE_COUNTS.values()}
        assert {"गायत्री", "उष्णिक्", "अनुष्टुभ्", "बृहती", "पङ्क्ति", "त्रिष्टुभ्", "जगती"} <= names
        assert vocab.VEDIC_SYLLABLE_COUNTS[24][0] == "गायत्री"

    def test_unicode_ranges_are_ordered_pairs(self):
        assert all(start <= end for start, end in vocab.VEDIC_UNICODE_RANGES)


class TestClassify:
    def test_rigveda_line_without_dandas_is_vedic(self, classifier):
        kind, confidence, features = classifier.classify(RV_1_1_1)
        assert kind == "vedic"
        assert confidence > 0.9
        assert features["likely_meter"] == "गायत्री"

    def test_gita_verse_with_dandas_is_classical(self, classifier):
        kind, confidence, features = classifier.classify(GITA_1_1)
        assert kind == "classical"
        assert confidence > 0.8
        assert features["structural_markers"] >= 1

    def test_scores_are_normalised(self, classifier):
        _kind, _confidence, features = classifier.classify(GITA_1_1)
        assert features["vedic_score"] + features["classical_score"] == pytest.approx(1.0)

    def test_vedic_unicode_marks_count(self, classifier):
        count, chars = classifier.check_vedic_unicode("अ॒ग्निमी॑ळे")
        assert count == 3
        assert set(chars) == {"॒", "॑", "ळ"}

    def test_structural_markers_find_verse_numbers(self, classifier):
        count, matches = classifier.check_structural_markers("धर्मक्षेत्रे ॥ १ ॥ \n इति गीता ॥")
        assert count >= 1
        assert matches

    def test_batch_matches_single_calls(self, classifier):
        assert classifier.classify_batch([RV_1_1_1, GITA_1_1]) == [
            classifier.classify(RV_1_1_1),
            classifier.classify(GITA_1_1),
        ]

    def test_module_helpers(self):
        assert tc.get_mode(RV_1_1_1) == "vedic"
        assert tc.is_vedic(RV_1_1_1) and not tc.is_classical(RV_1_1_1)
        assert tc.classify_text(GITA_1_1)[0] == "classical"
        assert tc.get_classifier() is tc.get_classifier()


class TestScoringHelpers:
    def test_normalize_scores(self):
        assert tc.TextClassifier._normalize_scores(0.3, 0.1, 0, 0) == pytest.approx((0.75, 0.25))

    @pytest.mark.parametrize(
        ("single", "double", "expected"),
        [(0, 1, (0.3, 0.7)), (2, 0, (0.3, 0.7)), (1, 0, (0.7, 0.3))],
    )
    def test_normalize_without_evidence_leans_on_dandas(self, single, double, expected):
        assert tc.TextClassifier._normalize_scores(0.0, 0.0, single, double) == expected

    def test_compound_density(self):
        assert tc.TextClassifier._compound_density_score("शार्दूलविक्रीडितम्अतिदीर्घसमासः") == 0.1
        assert tc.TextClassifier._compound_density_score("राम सीता") == 0.0
        assert tc.TextClassifier._compound_density_score("") == 0.0

    def test_line_regularity_needs_two_even_lines(self, classifier):
        assert classifier._line_regularity_score(RV_1_1_1) == 0.0
        regular = "न तातो न माता न बन्धुर्न दाता।\nन पुत्रो न पुत्री न भृत्यो न भर्ता।"
        assert classifier._line_regularity_score(regular) == 0.2
        uneven = "राम।\nअतिदीर्घपङ्क्तिः यत्र बहूनि अक्षराणि सन्ति इति।"
        assert classifier._line_regularity_score(uneven) == 0.0

    def test_syllable_counters(self, classifier):
        assert classifier.count_syllables("धर्मक्षेत्रे") == 4
        assert classifier.count_syllables_fast("") == 1
