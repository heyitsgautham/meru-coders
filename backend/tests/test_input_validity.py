"""is_valid_sanskrit_input: which inputs reach the meter engine, and the reason given for each."""

import pytest

from backend.core.chanda_input_words import COMMON_ENGLISH_WORDS


def verdict(chanda, text):
    valid, reason = chanda.is_valid_sanskrit_input(text)
    return valid, reason[reason.rfind("(") + 1 : -1]


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("", (False, "Empty input")),
        ("ॐ", (True, "Om mantra")),
        ("AUM", (True, "Om mantra")),
        ("ab", (False, "Text too short - minimum 3 characters")),
        ("क", (False, "Text too short - minimum 2 characters for Indic script")),
        ("धर्मक्षेत्रे कुरुक्षेत्रे", (True, "Devanagari script detected")),
        ("अ॒ग्निमी॑ळे पु॒रोहि॑तं", (True, "Devanagari script detected")),
        ("రామాయణం", (True, "Indic script detected")),
        ("dharmakṣetre kurukṣetre", (True, "IAST transliteration detected")),
        ("dharmakSetre kurukSetre samavetA yuyutsavaH", (True, "Possible transliteration")),
        ("12345", (False, "No alphabetic characters found")),
        ("djajjkvdskldsjlsdfjkl", (False, "Invalid text - vowel ratio too low for Sanskrit")),
        ("bcdfg hjklm", (False, "Invalid text format")),
    ],
)
def test_verdicts(chanda, text, expected):
    assert verdict(chanda, text) == expected


@pytest.mark.parametrize("text", ["hello", "this is a test", "go to the market", "dharma the karma"])
def test_english_without_diacritics_is_rejected(chanda, text):
    assert verdict(chanda, text) == (False, "Appears to be English text - Sanskrit IAST requires diacritical marks")


def test_diacritics_let_an_odd_english_word_through(chanda):
    assert verdict(chanda, "ārya the") == (True, "IAST transliteration detected")


def test_mostly_english_with_diacritics_is_still_rejected(chanda):
    assert verdict(chanda, "ṣaṭ the of and in") == (False, "Appears to be English text, not Sanskrit")


def test_word_list_is_lower_case_ascii():
    assert {"hello", "the", "go"} <= COMMON_ENGLISH_WORDS
    assert all(word.isascii() and word == word.lower() for word in COMMON_ENGLISH_WORDS)
