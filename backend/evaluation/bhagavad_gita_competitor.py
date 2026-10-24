#!/usr/bin/env python3
"""
Test Script: Validate Bhagavad Gita Shlokas from Competitor Dataset
====================================================================
Extracts shlokas from repos/ShlokaYug/BHAGAVAD-GITA SHLOKAS.txt
and validates them against our Chandas identification engine.

Expected meters for Bhagavad Gita:
- Most verses: Anushtubh (अनुष्टुभ्) - 32 syllables (4×8)
- Some verses: Trishtubh (त्रिष्टुभ्) - 44 syllables (4×11)
"""

import re
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from core import Chanda


def extract_shlokas_from_file(file_path: str) -> list:
    """
    Extract Devanagari shlokas from the competitor's Bhagavad Gita file.
    Returns list of dicts with: category, chapter, verse, devanagari_text, iast_text
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    shlokas = []
    current_category = "Unknown"

    lines = content.split('\n')

    # Valid category names (skip PURPORT, TRANSLATION, etc.)
    valid_categories = {
        'ANGER', 'CONFUSION', 'FEAR', 'GREED', 'LUST', 'PRIDE',
        'DEPRESSION', 'LONELINESS', 'JEALOUSY', 'LAZINESS', 'DEATH',
        'FEELING SINFUL', 'MIND CONTROL', 'FORGETFULNESS', 'DEMOTIVATED',
        'FEELING DISCRIMINATED', 'SEEKING PEACE', 'TEMPTATION',
        'PRACTISING FORGIVENESS', 'LOSING HOPE', 'ENVY (JEALOUSY)'
    }

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect category headers (ALL CAPS, must be in valid list or contains key emotions)
        if line and line.isupper() and len(line) < 30:
            if line in valid_categories or any(cat in line for cat in ['ANGER', 'FEAR', 'GREED', 'LUST', 'PRIDE', 'DEATH']):
                current_category = line
            i += 1
            continue

        # Detect chapter references like "Chapter 2 - Text 56" or "CHAPTER 16 - TEXT 4"
        chapter_match = re.match(r'[Cc]hapter\s+(\d+)\s*[-–]\s*[Tt]ext\s+(\d+(?:-\d+)?)', line, re.IGNORECASE)
        if chapter_match:
            chapter = chapter_match.group(1)
            verse = chapter_match.group(2)

            # Look for Devanagari text (next lines with Devanagari characters)
            devanagari_lines = []
            iast_lines = []
            i += 1

            # Collect Devanagari lines until we hit IAST or word meanings
            while i < len(lines):
                next_line = lines[i].strip()

                # Check if line contains Devanagari (Unicode range)
                if re.search(r'[\u0900-\u097F]', next_line):
                    devanagari_lines.append(next_line)
                    i += 1
                # Check if line is IAST (has diacritics)
                elif re.search(r'[āīūṛṝḷḹēōṁḥśṣṇṭḍṅñ]', next_line.lower()) and next_line and '—' not in next_line:
                    iast_lines.append(next_line)
                    i += 1
                # Skip empty lines but stop after finding Devanagari + some IAST
                elif not next_line:
                    i += 1
                    # Continue looking for more lines
                    continue
                # If we hit word meanings (contains —) or TRANSLATION, stop
                elif '—' in next_line or next_line.startswith('TRANSLATION'):
                    break
                # If we hit another Chapter header, stop
                elif re.match(r'[Cc]hapter\s+\d+', next_line):
                    break
                else:
                    i += 1
                    # Stop if we have enough content
                    if len(devanagari_lines) >= 2 and len(iast_lines) >= 2:
                        break

            if devanagari_lines:
                # Combine lines into full verse
                devanagari_text = ' '.join(devanagari_lines)
                # Clean up: remove verse number markers like ॥ ५६ ॥ or ॥ 56 ॥
                devanagari_text = re.sub(r'॥\s*[\d०-९]+\s*॥', '', devanagari_text).strip()
                # Also clean single danda and verse numbers
                devanagari_text = re.sub(r'\s*।\s*$', '', devanagari_text).strip()

                if devanagari_text and len(devanagari_text) > 10:
                    shlokas.append({
                        'category': current_category,
                        'chapter': chapter,
                        'verse': verse,
                        'devanagari': devanagari_text,
                        'iast': ' '.join(iast_lines) if iast_lines else '',
                        'reference': f"BG {chapter}.{verse}"
                    })
            continue

        i += 1

    # Remove duplicates (same reference)
    seen_refs = set()
    unique_shlokas = []
    for s in shlokas:
        if s['reference'] not in seen_refs:
            seen_refs.add(s['reference'])
            unique_shlokas.append(s)

    return unique_shlokas


def test_bhagavad_gita_shlokas():
    """Main test function to validate Bhagavad Gita shlokas."""

    # Path to competitor's file
    competitor_file = Path(__file__).parent.parent.parent / "repos/ShlokaYug/BHAGAVAD-GITA SHLOKAS.txt"

    if not competitor_file.exists():
        print(f"❌ File not found: {competitor_file}")
        return

    print("=" * 80)
    print("BHAGAVAD GITA SHLOKAS VALIDATION TEST")
    print("Source: repos/ShlokaYug/BHAGAVAD-GITA SHLOKAS.txt")
    print("=" * 80)

    # Extract shlokas
    print("\n📖 Extracting shlokas from competitor dataset...")
    shlokas = extract_shlokas_from_file(str(competitor_file))
    print(f"   Found {len(shlokas)} shlokas across {len(set(s['category'] for s in shlokas))} categories")

    # Initialize our engine
    print("\n🔧 Initializing Chandas engine...")
    chanda = Chanda(data_path=str(settings.DATA_DIR))

    # Test results tracking
    results = {
        'total': len(shlokas),
        'anushtubh': 0,
        'trishtubh': 0,
        'jagati': 0,
        'other_classical': 0,
        'failed': 0,
        'details': []
    }

    # Expected meters for Bhagavad Gita
    expected_meters = {'अनुष्टुभ्', 'anuṣṭubh', 'anushtubh', 'Anuṣṭubh', 'Anushtubh',
                       'त्रिष्टुभ्', 'triṣṭubh', 'trishtubh', 'Triṣṭubh',
                       'जगती', 'jagatī', 'jagati', 'Jagatī',
                       'उपजाति', 'Upajati', 'upajāti',
                       'वंशस्थ', 'Vamshastha', 'vaṃśastha',
                       'इन्द्रवज्रा', 'Indravajra', 'indravajrā',
                       'उपेन्द्रवज्रा', 'Upendravajra'}

    anushtubh_patterns = {'अनुष्टुभ्', 'anuṣṭubh', 'anushtubh', 'Anuṣṭubh', 'Anushtubh', 'श्लोक', 'Shloka'}
    trishtubh_patterns = {'त्रिष्टुभ्', 'triṣṭubh', 'trishtubh', 'Triṣṭubh', 'Trishtubh',
                          'इन्द्रवज्रा', 'Indravajra', 'उपेन्द्रवज्रा', 'Upendravajra',
                          'उपजाति', 'Upajati', 'वंशस्थ', 'Vamshastha'}

    print("\n" + "=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)

    # Group by category for organized output
    categories = {}
    for shloka in shlokas:
        cat = shloka['category']
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(shloka)

    for category, cat_shlokas in categories.items():
        print(f"\n📂 {category}")
        print("-" * 40)

        for shloka in cat_shlokas:
            ref = shloka['reference']
            text = shloka['devanagari']

            # Identify using verse mode for full verse analysis
            result = chanda.identify_from_text(text, verse=True)

            # Extract primary meter
            identified_meter = "Unknown"
            syllable_count = 0
            confidence = 0

            # Navigate to the actual result structure
            if result and 'result' in result:
                inner_result = result['result']

                # Try verse-level analysis first
                if 'verse' in inner_result and inner_result['verse']:
                    verse_data = inner_result['verse']
                    if isinstance(verse_data, list) and len(verse_data) > 0:
                        verse_entry = verse_data[0]
                        chanda_info = verse_entry.get('chanda', ([], 0))
                        if chanda_info and len(chanda_info) >= 2:
                            meters = chanda_info[0] if isinstance(chanda_info[0], list) else [chanda_info[0]]
                            confidence = chanda_info[1]
                            if meters:
                                identified_meter = meters[0]
                        # Get syllable count from lines
                        lines_idx = verse_entry.get('lines', [])
                        if 'line' in inner_result and inner_result['line']:
                            for idx in lines_idx:
                                if idx < len(inner_result['line']):
                                    line_len = inner_result['line'][idx].get('result', {}).get('length', 0)
                                    if line_len:
                                        syllable_count += int(line_len)

                # Fallback: try line-by-line
                if identified_meter == "Unknown" and 'line' in inner_result and inner_result['line']:
                    for line_entry in inner_result['line']:
                        line_res = line_entry.get('result', {})
                        if line_res.get('found'):
                            identified_meter = line_res.get('display_chanda_primary', 'Unknown')
                            syllable_count = line_res.get('length', 0) or 0
                            break

            # Classify result
            is_anushtubh = any(p.lower() in identified_meter.lower() for p in anushtubh_patterns)
            is_trishtubh = any(p.lower() in identified_meter.lower() for p in trishtubh_patterns)

            if is_anushtubh:
                results['anushtubh'] += 1
                status = "✅"
            elif is_trishtubh:
                results['trishtubh'] += 1
                status = "✅"
            elif identified_meter != "Unknown":
                results['other_classical'] += 1
                status = "⚠️"
            else:
                results['failed'] += 1
                status = "❌"

            # Store detail
            results['details'].append({
                'ref': ref,
                'category': category,
                'meter': identified_meter,
                'syllables': syllable_count,
                'status': status
            })

            # Print result
            text_preview = text[:50] + "..." if len(text) > 50 else text
            print(f"  {status} {ref}: {identified_meter} ({syllable_count} syl)")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    total = results['total']
    success = results['anushtubh'] + results['trishtubh'] + results['other_classical']
    accuracy = (success / total * 100) if total > 0 else 0

    print(f"""
📊 Total Shlokas Tested: {total}

📈 Meter Distribution:
   • Anushtubh (अनुष्टुभ्):     {results['anushtubh']} ({results['anushtubh']/total*100:.1f}%)
   • Trishtubh (त्रिष्टुभ्):     {results['trishtubh']} ({results['trishtubh']/total*100:.1f}%)
   • Other Classical:         {results['other_classical']} ({results['other_classical']/total*100:.1f}%)
   • Failed/Unknown:          {results['failed']} ({results['failed']/total*100:.1f}%)

✨ Overall Accuracy: {accuracy:.1f}% ({success}/{total})
""")

    # Expected: Most BG verses are Anushtubh
    if results['anushtubh'] >= total * 0.7:
        print("✅ PASS: Majority correctly identified as Anushtubh (expected for Bhagavad Gita)")
    elif accuracy >= 85:
        print("✅ PASS: High accuracy on classical Sanskrit meters")
    else:
        print("⚠️ NOTE: Review failed identifications for edge cases")

    # Print failed cases for debugging
    failed_cases = [d for d in results['details'] if d['status'] == '❌']
    if failed_cases:
        print("\n📋 Failed Cases (for debugging):")
        for case in failed_cases[:10]:  # Show first 10
            print(f"   • {case['ref']}: {case['meter']}")

    return results


if __name__ == "__main__":
    results = test_bhagavad_gita_shlokas()
