"""Input screening before identification: the rule-based verdicts and the Gemini path with a fake client."""

import types as pytypes

import pytest

from backend.core import ai_validator
from backend.core.ai_validator_rules import rule_based_validation


@pytest.mark.parametrize(
    ("text", "valid", "action"),
    [
        ("", False, "reject"),
        ("hello world", False, "reject"),
        ("धर्मक्षेत्रे कुरुक्षेत्रे", True, "proceed"),
        ("dharmakṣetre kurukṣetre", True, "proceed"),
    ],
)
def test_rule_based_verdicts(text, valid, action):
    result = rule_based_validation(text)
    assert (result["is_valid"], result["action"], result["ai_validated"]) == (valid, action, False)


def test_the_old_private_name_still_works():
    assert ai_validator._rule_based_validation is rule_based_validation


def test_a_disabled_validator_uses_the_rules():
    validator = ai_validator.AIShlokaValidator(enabled=False)
    assert validator.validate_shloka("hello world") == rule_based_validation("hello world")


def fake_client(reply):
    def generate_content(model, contents, config):
        if isinstance(reply, Exception):
            raise reply
        return pytypes.SimpleNamespace(text=reply)

    return pytypes.SimpleNamespace(models=pytypes.SimpleNamespace(generate_content=generate_content))


@pytest.fixture
def enabled_validator(monkeypatch):
    validator = ai_validator.AIShlokaValidator(enabled=False)
    validator.enabled = True
    return validator


def test_gemini_verdict_is_parsed_from_fenced_json(enabled_validator, monkeypatch):
    reply = '```json\n{"is_valid_shloka": false, "confidence": 0.9, "text_type": "prose", "reason": "Prose", "suggested_action": "reject"}\n```'
    monkeypatch.setattr(enabled_validator, "_get_client", lambda: fake_client(reply))
    result = enabled_validator.validate_shloka("गद्यम् इदम्")
    assert result == {
        "is_valid": False,
        "confidence": 0.9,
        "text_type": "prose",
        "reason": "Prose",
        "action": "reject",
        "ai_validated": True,
    }
    assert enabled_validator.should_proceed_with_identification(result) == (
        False,
        "अमान्य आदान: Prose (Invalid input: Prose)",
    )


@pytest.mark.parametrize("reply", ["not json", RuntimeError("network down"), ""])
def test_gemini_failures_fall_back_to_the_rules(enabled_validator, monkeypatch, reply):
    monkeypatch.setattr(enabled_validator, "_get_client", lambda: fake_client(reply))
    assert enabled_validator.validate_shloka("hello world") == rule_based_validation("hello world")


def test_long_texts_skip_gemini(enabled_validator, monkeypatch):
    monkeypatch.setattr(enabled_validator, "_get_client", lambda: pytest.fail("Gemini must not be called"))
    assert enabled_validator.validate_shloka("क" * 2001)["ai_validated"] is False


def test_skip_ai_always_proceeds():
    assert ai_validator.validate_shloka_input("anything", skip_ai=True)[:2] == (True, None)
