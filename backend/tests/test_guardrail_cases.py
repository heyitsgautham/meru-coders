"""The chatbot guardrail smoke cases load from their JSON file intact."""

from collections import Counter

# Imported as a module: its TestCase and TestCategory classes would look like test classes to pytest.
from backend.scripts.smoke import chatbot_guardrails as guardrails


def test_every_case_loads_with_a_known_category_and_expectation():
    cases = guardrails.load_test_cases()
    assert [case.id for case in cases] == list(range(1, 51))
    assert {case.category for case in cases} == set(guardrails.TestCategory)
    assert Counter(case.expected_behavior for case in cases)[guardrails.ExpectedBehavior.REJECT_REDIRECT] > 0
    assert all(case.message.strip() for case in cases)
