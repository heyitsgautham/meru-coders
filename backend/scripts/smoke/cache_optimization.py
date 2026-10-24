#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for cache-based AI skip optimization.
Compares latency for cache hits vs cache misses.

Run: python tests/test_cache_optimization.py
"""

import os
import statistics
import sys
import time

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

BASE_URL = "http://localhost:5000/api"

# Test verses - mix of known (cached) and variations
TEST_CASES = [
    # Known verses from Rigveda (should be in cache)
    {
        "name": "Rigveda 1.1.1 (Gayatri)",
        "text": "अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं",
        "expected_cache_hit": True,
        "expected_meter": "gāyatrī",
    },
    {
        "name": "Rigveda 1.1.3",
        "text": "अग्निना रयिमश्नवत्पोषमेव दिवेदिवे यशसं वीरवत्तमं",
        "expected_cache_hit": True,
        "expected_meter": "gāyatrī",
    },
    # Bhagavad Gita verses (should be in chandovallari or similar)
    {
        "name": "BG 1.1 (Anushtubh)",
        "text": "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः",
        "expected_cache_hit": False,  # May or may not be cached
        "expected_meter": "अनुष्टुभ्",
    },
    # Made up verse (definitely NOT in cache)
    {
        "name": "Novel verse (no cache)",
        "text": "काव्यं करोति कविः सुन्दरं वचनं रम्यम्",
        "expected_cache_hit": False,
        "expected_meter": None,  # Unknown
    },
    # Mandakranta from chandovallari (likely cached)
    {
        "name": "Mandakranta sample",
        "text": "श्यामास्वाङ्गं चकितहरिणीप्रेक्षणे दृष्टिपातं",
        "expected_cache_hit": True,
        "expected_meter": "mandākrāntā",
    },
]


def test_single_verse(verse_data):
    """Test a single verse and return timing info."""
    url = f"{BASE_URL}/identify/text"
    payload = {"text": verse_data["text"], "text_mode": "line"}

    start = time.time()
    try:
        response = requests.post(url, json=payload, timeout=30)
        elapsed_ms = (time.time() - start) * 1000

        if response.status_code != 200:
            return {
                "name": verse_data["name"],
                "success": False,
                "error": f"HTTP {response.status_code}",
                "elapsed_ms": elapsed_ms,
            }

        data = response.json()
        timing = data.get("timing", {})
        cache_info = data.get("cache_info", {})

        return {
            "name": verse_data["name"],
            "success": data.get("success", False),
            "elapsed_total_ms": elapsed_ms,
            "server_total_ms": timing.get("total_ms", 0),
            "cache_lookup_ms": timing.get("cache_lookup_ms", 0),
            "ai_validation_ms": timing.get("ai_validation_ms", 0),
            "rule_engine_ms": timing.get("rule_engine_ms", 0),
            "cache_hit": timing.get("cache_hit", False),
            "ai_skipped": timing.get("ai_skipped", False),
            "similarity": cache_info.get("similarity", 0),
            "cached_chandas": cache_info.get("cached_chandas", ""),
            "expected_cache_hit": verse_data.get("expected_cache_hit"),
            "identified_meter": data.get("summary", {}).get("line", {}).get("match", {}).get("chanda", {}),
        }

    except Exception as e:
        return {
            "name": verse_data["name"],
            "success": False,
            "error": str(e),
            "elapsed_ms": (time.time() - start) * 1000,
        }


def run_benchmark(iterations=3):
    """Run benchmark with multiple iterations."""
    print("=" * 70)
    print("CACHE OPTIMIZATION BENCHMARK")
    print("=" * 70)
    print(f"Running {iterations} iterations for each test case...\n")

    all_results = []

    for verse in TEST_CASES:
        print(f"\n📝 Testing: {verse['name']}")
        print(f"   Text: {verse['text'][:50]}...")

        verse_results = []
        for i in range(iterations):
            result = test_single_verse(verse)
            verse_results.append(result)

            # Small delay between requests
            time.sleep(0.1)

        # Calculate averages
        successful = [r for r in verse_results if r.get("success")]
        if successful:
            avg_total = statistics.mean([r["server_total_ms"] for r in successful])
            avg_cache = statistics.mean([r["cache_lookup_ms"] for r in successful])
            avg_ai = statistics.mean([r["ai_validation_ms"] for r in successful])
            avg_rule = statistics.mean([r["rule_engine_ms"] for r in successful])

            cache_hit = successful[0].get("cache_hit", False)
            ai_skipped = successful[0].get("ai_skipped", False)
            similarity = successful[0].get("similarity", 0)

            print(f"   ✓ Cache Hit: {cache_hit} (similarity: {similarity:.2%})")
            print(f"   ✓ AI Skipped: {ai_skipped}")
            print(f"   ⏱️  Avg Total: {avg_total:.1f}ms")
            print(f"      - Cache lookup: {avg_cache:.1f}ms")
            print(f"      - AI validation: {avg_ai:.1f}ms {'(SKIPPED)' if ai_skipped else ''}")
            print(f"      - Rule engine: {avg_rule:.1f}ms")

            all_results.append(
                {
                    "name": verse["name"],
                    "cache_hit": cache_hit,
                    "ai_skipped": ai_skipped,
                    "avg_total_ms": avg_total,
                    "avg_cache_ms": avg_cache,
                    "avg_ai_ms": avg_ai,
                    "avg_rule_ms": avg_rule,
                    "similarity": similarity,
                }
            )
        else:
            print("   ❌ All iterations failed!")
            if verse_results:
                print(f"   Error: {verse_results[0].get('error', 'Unknown')}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    cache_hits = [r for r in all_results if r.get("cache_hit")]
    cache_misses = [r for r in all_results if not r.get("cache_hit")]

    if cache_hits:
        avg_hit_time = statistics.mean([r["avg_total_ms"] for r in cache_hits])
        print(f"\n🎯 CACHE HITS ({len(cache_hits)} cases):")
        print(f"   Average total time: {avg_hit_time:.1f}ms")
        for r in cache_hits:
            print(f"   - {r['name']}: {r['avg_total_ms']:.1f}ms (AI {'skipped' if r['ai_skipped'] else 'ran'})")

    if cache_misses:
        avg_miss_time = statistics.mean([r["avg_total_ms"] for r in cache_misses])
        print(f"\n❌ CACHE MISSES ({len(cache_misses)} cases):")
        print(f"   Average total time: {avg_miss_time:.1f}ms")
        for r in cache_misses:
            print(f"   - {r['name']}: {r['avg_total_ms']:.1f}ms")

    if cache_hits and cache_misses:
        speedup = avg_miss_time / avg_hit_time if avg_hit_time > 0 else 0
        savings = avg_miss_time - avg_hit_time
        print("\n⚡ OPTIMIZATION IMPACT:")
        print(f"   Speedup: {speedup:.1f}x faster for cached verses")
        print(f"   Time saved: {savings:.1f}ms per request")
        print(
            f"   AI calls avoided: {len(cache_hits)} / {len(all_results)} ({100 * len(cache_hits) / len(all_results):.0f}%)"
        )

    return all_results


def test_api_available():
    """Check if API is running."""
    try:
        response = requests.get(f"{BASE_URL}/info", timeout=5)
        return response.status_code == 200
    except:
        return False


if __name__ == "__main__":
    print("Checking API availability...")
    if not test_api_available():
        print("❌ API not available at", BASE_URL)
        print("Please start the backend server: cd backend && python run.py")
        sys.exit(1)

    print("✓ API is running\n")

    # Run benchmark
    results = run_benchmark(iterations=3)

    print("\n" + "=" * 70)
    print("Test completed!")
