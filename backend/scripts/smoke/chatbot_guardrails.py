"""
Comprehensive Guardrails Testing for Chandas Chatbot (50 Test Cases)
Tests cover jailbreak attempts, out-of-scope requests, and legitimate use cases
Author: Meru Coders Team
Date: December 6, 2025
"""

import json
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Tuple

import requests

# Configuration
API_BASE_URL = "http://localhost:5000"
CHATBOT_ENDPOINT = f"{API_BASE_URL}/api/chatbot/chat"


class TestCategory(Enum):
    """Test categories for organization"""

    JAILBREAK_DIRECT = "Direct Jailbreak Attempt"
    JAILBREAK_SUBTLE = "Subtle Jailbreak Attempt"
    OUT_OF_SCOPE = "Out of Scope Request"
    LEGITIMATE = "Legitimate Use Case"
    EDGE_CASE = "Edge Case"
    MULTILINGUAL = "Multilingual Jailbreak"


class ExpectedBehavior(Enum):
    """Expected chatbot responses"""

    REJECT_REDIRECT = "Should reject and redirect to Sanskrit prosody"
    COMPLY = "Should comply with legitimate request"
    PARTIAL_COMPLY = "Should partially comply with context redirection"


@dataclass
class TestCase:
    """Structure for test cases"""

    id: int
    category: TestCategory
    persona: str
    message: str
    expected_behavior: ExpectedBehavior
    description: str
    keywords_must_have: List[str]  # Keywords that should appear in response
    keywords_must_not_have: List[str]  # Keywords that should NOT appear


# The 50 cases live in chatbot_guardrail_cases.json beside this script, in id order.
CASES_FILE = Path(__file__).with_name("chatbot_guardrail_cases.json")


def load_test_cases(path: Path = CASES_FILE) -> List[TestCase]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    return [
        TestCase(
            **{
                **row,
                "category": TestCategory[row["category"]],
                "expected_behavior": ExpectedBehavior[row["expected_behavior"]],
            }
        )
        for row in rows
    ]


TEST_CASES = load_test_cases()

# ============================================================================
# TEST EXECUTION ENGINE
# ============================================================================


class GuardrailTester:
    """Execute and analyze guardrail tests"""

    def __init__(self, endpoint: str = CHATBOT_ENDPOINT):
        self.endpoint = endpoint
        self.results = []
        self.stats = {"total": 0, "passed": 0, "failed": 0, "errors": 0, "by_category": {}, "by_persona": {}}

    def send_message(self, message: str, persona: str) -> Dict:
        """Send message to chatbot API"""
        try:
            response = requests.post(self.endpoint, json={"message": message, "persona": persona}, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e)}

    def check_keywords(self, text: str, must_have: List[str], must_not_have: List[str]) -> Tuple[bool, List[str]]:
        """Check if response contains required keywords and avoids forbidden ones"""
        text_lower = text.lower()
        issues = []

        # Check must-have keywords
        for keyword in must_have:
            if keyword.lower() not in text_lower:
                issues.append(f"Missing required keyword: '{keyword}'")

        # Check must-not-have keywords
        for keyword in must_not_have:
            if keyword.lower() in text_lower:
                issues.append(f"Contains forbidden keyword: '{keyword}'")

        return len(issues) == 0, issues

    def run_test(self, test_case: TestCase) -> Dict:
        """Execute a single test case"""
        print(f"\n{'=' * 80}")
        print(f"TEST {test_case.id}: {test_case.description}")
        print(f"Category: {test_case.category.value} | Persona: {test_case.persona}")
        print(f"Message: {test_case.message}")
        print(f"{'=' * 80}")

        # Send message
        response = self.send_message(test_case.message, test_case.persona)

        if "error" in response:
            print(f"❌ ERROR: {response['error']}")
            return {"test_id": test_case.id, "status": "ERROR", "error": response['error'], "test_case": test_case}

        # Extract response text
        response_text = response.get("response", "")
        print(f"\nResponse: {response_text[:200]}{'...' if len(response_text) > 200 else ''}")

        # Check keywords
        passed, issues = self.check_keywords(
            response_text, test_case.keywords_must_have, test_case.keywords_must_not_have
        )

        # Determine pass/fail
        if passed:
            print("✅ PASSED")
            status = "PASSED"
        else:
            print("❌ FAILED")
            for issue in issues:
                print(f"   - {issue}")
            status = "FAILED"

        return {
            "test_id": test_case.id,
            "status": status,
            "response": response_text,
            "issues": issues,
            "test_case": test_case,
        }

    def run_all_tests(self, delay_between_tests: float = 0.5):
        """Execute all test cases"""
        print("\n" + "=" * 80)
        print("CHANDAS CHATBOT GUARDRAILS TEST SUITE - 50 COMPREHENSIVE TESTS")
        print("=" * 80)

        for test_case in TEST_CASES:
            result = self.run_test(test_case)
            self.results.append(result)

            # Update statistics
            self.stats["total"] += 1
            if result["status"] == "PASSED":
                self.stats["passed"] += 1
            elif result["status"] == "FAILED":
                self.stats["failed"] += 1
            else:
                self.stats["errors"] += 1

            # Category stats
            category = test_case.category.value
            if category not in self.stats["by_category"]:
                self.stats["by_category"][category] = {"passed": 0, "failed": 0, "errors": 0}
            self.stats["by_category"][category][result["status"].lower()] += 1

            # Persona stats
            persona = test_case.persona
            if persona not in self.stats["by_persona"]:
                self.stats["by_persona"][persona] = {"passed": 0, "failed": 0, "errors": 0}
            self.stats["by_persona"][persona][result["status"].lower()] += 1

            # Delay to avoid rate limiting
            time.sleep(delay_between_tests)

        self.print_summary()
        self.save_results()

    def print_summary(self):
        """Print test execution summary"""
        print("\n" + "=" * 80)
        print("TEST EXECUTION SUMMARY")
        print("=" * 80)

        # Overall stats
        total = self.stats["total"]
        passed = self.stats["passed"]
        failed = self.stats["failed"]
        errors = self.stats["errors"]
        pass_rate = (passed / total * 100) if total > 0 else 0

        print("\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total}")
        print(f"   ✅ Passed: {passed} ({pass_rate:.1f}%)")
        print(f"   ❌ Failed: {failed} ({(failed / total * 100) if total > 0 else 0:.1f}%)")
        print(f"   🚫 Errors: {errors} ({(errors / total * 100) if total > 0 else 0:.1f}%)")

        # Category breakdown
        print("\n📂 RESULTS BY CATEGORY:")
        for category, stats in self.stats["by_category"].items():
            cat_total = stats["passed"] + stats["failed"] + stats["errors"]
            cat_pass_rate = (stats["passed"] / cat_total * 100) if cat_total > 0 else 0
            print(f"   {category}:")
            print(f"      ✅ {stats['passed']}/{cat_total} ({cat_pass_rate:.1f}%)")

        # Persona breakdown
        print("\n👤 RESULTS BY PERSONA:")
        for persona, stats in self.stats["by_persona"].items():
            per_total = stats["passed"] + stats["failed"] + stats["errors"]
            per_pass_rate = (stats["passed"] / per_total * 100) if per_total > 0 else 0
            print(f"   {persona}:")
            print(f"      ✅ {stats['passed']}/{per_total} ({per_pass_rate:.1f}%)")

        # Failed tests detail
        failed_tests = [r for r in self.results if r["status"] == "FAILED"]
        if failed_tests:
            print("\n❌ FAILED TESTS DETAIL:")
            for result in failed_tests:
                tc = result["test_case"]
                print(f"   Test {tc.id}: {tc.description}")
                for issue in result.get("issues", []):
                    print(f"      - {issue}")

        # Error tests detail
        error_tests = [r for r in self.results if r["status"] == "ERROR"]
        if error_tests:
            print("\n🚫 ERROR TESTS DETAIL:")
            for result in error_tests:
                tc = result["test_case"]
                print(f"   Test {tc.id}: {tc.description}")
                print(f"      Error: {result.get('error', 'Unknown error')}")

        print("\n" + "=" * 80)

    def save_results(self, filename: str = "guardrail_test_results.json"):
        """Save test results to JSON file"""
        output = {
            "timestamp": datetime.now().isoformat(),
            "summary": self.stats,
            "tests": [
                {
                    "id": r["test_id"],
                    "status": r["status"],
                    "category": r["test_case"].category.value,
                    "persona": r["test_case"].persona,
                    "description": r["test_case"].description,
                    "message": r["test_case"].message,
                    "response": r.get("response", ""),
                    "issues": r.get("issues", []),
                    "error": r.get("error", None),
                }
                for r in self.results
            ],
        }

        filepath = Path(__file__).with_name(filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)

        print(f"\n💾 Results saved to: {filepath}")


# ============================================================================
# MAIN EXECUTION
# ============================================================================


def main():
    """Main test execution"""
    print("\n🚀 Starting Chandas Chatbot Guardrails Test Suite...")
    print("⏳ This will take approximately 30-60 seconds to complete all 50 tests.\n")

    # Check if server is running
    try:
        requests.get(f"{API_BASE_URL}/api/identify/text", timeout=5)
    except Exception:
        print("❌ ERROR: Backend server is not running!")
        print("Please start the server with: cd backend && python run.py")
        return

    # Run tests
    tester = GuardrailTester()
    tester.run_all_tests(delay_between_tests=0.5)

    print("\n✨ Test suite completed!")


if __name__ == "__main__":
    main()
