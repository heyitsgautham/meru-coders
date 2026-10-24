"""Unit tests for the pure helpers in backend.api.chatbot.

These replace an older test file that exercised a pasted copy of
detect_meter_intent instead of the real function.
"""

import pytest

from backend.api import chatbot


class TestExtractSanskritText:
    def test_quoted_text_wins(self):
        message = 'Identify the meter of "rāmo rājamaṇiḥ" please'
        assert chatbot.extract_sanskrit_text(message) == "rāmo rājamaṇiḥ"

    def test_longest_devanagari_span_without_danda(self):
        message = "What is the meter of धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः।"
        assert chatbot.extract_sanskrit_text(message) == "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"

    def test_single_short_word(self):
        assert chatbot.extract_sanskrit_text("meaning of राम") == "राम"

    def test_no_sanskrit(self):
        assert chatbot.extract_sanskrit_text("hello there") is None


class TestDetectMeterIntent:
    def test_no_intent_for_greeting(self):
        has_intent, text, fields = chatbot.detect_meter_intent("hello, how are you?")
        assert has_intent is False
        assert text is None
        assert not any(fields.values())

    def test_full_analysis_when_no_field_named(self):
        has_intent, text, fields = chatbot.detect_meter_intent("identify धर्मक्षेत्रे कुरुक्षेत्रे")
        assert has_intent is True
        assert text == "धर्मक्षेत्रे कुरुक्षेत्रे"
        assert fields["full_analysis"] is True

    @pytest.mark.parametrize(
        ("message", "field"),
        [
            ("what is the meter name of this", "meter_name"),
            ("show the laghu guru pattern", "lg_pattern"),
            ("which gana does this meter use", "gana_pattern"),
            ("count each syllable of this meter", "syllable_count"),
            ("give the matra count for this meter", "matra_count"),
        ],
    )
    def test_specific_field_requests(self, message, field):
        has_intent, _, fields = chatbot.detect_meter_intent(message)
        assert has_intent is True
        assert fields[field] is True
        assert fields["full_analysis"] is False


class TestExtractPrimaryMeterName:
    def test_pipe_separated_display(self):
        display = "इन्द्रवज्रा (indravajrā) [10.0] | त्रिष्टुभ् (पाद 1) [8.0]"
        assert chatbot.extract_primary_meter_name(display) == "इन्द्रवज्रा"

    def test_slash_separated_display(self):
        display = "अनुष्टुभ् (पाद 1-2) / अनुष्टुभ् (पाद 3-4)"
        assert chatbot.extract_primary_meter_name(display) == "अनुष्टुभ्"

    def test_transliteration_only_kept(self):
        assert chatbot.extract_primary_meter_name("(anuṣṭubh) [9.5]") == "(anuṣṭubh)"

    @pytest.mark.parametrize("display", ["", None])
    def test_empty_display(self, display):
        assert chatbot.extract_primary_meter_name(display) == "Unknown"


@pytest.mark.parametrize(
    ("score", "label"),
    [(10.0, "Very High"), (9.0, "Very High"), (7.5, "High"), (5.0, "Medium"), (3.0, "Low"), (0.5, "Very Low")],
)
def test_get_confidence_label(score, label):
    assert chatbot.get_confidence_label(score) == label


class TestSplitLgPatternByPada:
    def test_splits_into_four_padas(self):
        result = chatbot.split_lg_pattern_by_pada("LGLGLGLG")
        assert result.splitlines() == [
            "- **Pada 1:** LG",
            "- **Pada 2:** LG",
            "- **Pada 3:** LG",
            "- **Pada 4:** LG",
        ]

    def test_splits_into_two_padas_when_not_divisible_by_four(self):
        assert chatbot.split_lg_pattern_by_pada("LLGGLG").splitlines() == [
            "- **Pada 1:** LLG",
            "- **Pada 2:** GLG",
        ]

    def test_odd_length_stays_on_one_line(self):
        assert chatbot.split_lg_pattern_by_pada("LGL") == "LGL"

    def test_explicit_pada_size(self):
        assert chatbot.split_lg_pattern_by_pada("LLLGGG", syllables_per_pada=3).count("Pada") == 2

    def test_empty(self):
        assert chatbot.split_lg_pattern_by_pada("") == ""


def test_format_lg_padas():
    assert chatbot.format_lg_padas(["LG", "GL"]) == "- **Pada 1:** LG\n- **Pada 2:** GL"
    assert chatbot.format_lg_padas([]) == ""


class TestFormatMeterResponse:
    def test_invalid_input_message(self):
        response = chatbot.format_meter_response({"success": False, "is_valid_input": False})
        assert response.startswith("**Invalid Input**")

    def test_generic_error_message(self):
        response = chatbot.format_meter_response({"success": False, "error": "boom"})
        assert "boom" in response

    def test_not_found_mentions_text(self):
        meter_data = {
            "success": True,
            "found": False,
            "text": "कखग",
            "syllables": 3,
            "lg_pattern": "LLL",
            "gana_pattern": "न",
            "matra": 3,
            "fuzzy_matches": [("मधुमती", 0.66)],
        }
        response = chatbot.format_meter_response(meter_data)
        assert "could not definitively identify" in response
        assert "Syllable count: **3**" in response
        assert "मधुमती (similarity: 0.66)" in response


def test_analyze_meter_agentic_identifies_anushtubh_half_verse():
    result = chatbot.analyze_meter_agentic("धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः")

    assert result["success"] is True
    assert result["found"] is True
    assert "अनुष्टुभ्" in result["meter"]
