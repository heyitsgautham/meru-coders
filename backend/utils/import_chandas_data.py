#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import meter data from sanskrit-coders/chandas JSON files to our CSV format

This script converts the meter data from the chandas repository into our
existing CSV format for integration into the Chandojñānam project.
"""

import csv
import json
import re
from pathlib import Path


def clean_pattern(pattern_str):
    """Clean up pattern string by removing spaces, dashes, etc."""
    if not pattern_str:
        return ''
    # Remove spaces, em dashes, en dashes
    cleaned = pattern_str.replace(' ', '').replace('—', '').replace('–', '')
    # Convert to uppercase
    cleaned = cleaned.upper()
    return cleaned


def calculate_syllables(pattern):
    """Calculate syllable count from L-G pattern"""
    if not pattern or not re.match(r'^[LG]+$', pattern):
        return 0
    return len(pattern)


def calculate_matra(pattern):
    """Calculate matra count: L=1, G=2"""
    if not pattern or not re.match(r'^[LG]+$', pattern):
        return 0
    return sum(1 if c == 'L' else 2 for c in pattern)


def convert_to_gana_notation(pattern):
    """Convert L-G pattern to gana notation (य र त न भ ज स म)"""
    gana_map = {
        'LGG': 'य',
        'GLG': 'र',
        'GGL': 'त',
        'LLL': 'न',
        'GLL': 'भ',
        'LGL': 'ज',
        'LLG': 'स',
        'GGG': 'म'
    }

    if not pattern or not re.match(r'^[LG]+$', pattern):
        return ''

    gana_str = ''
    i = 0
    while i < len(pattern):
        if i + 3 <= len(pattern):
            triplet = pattern[i:i+3]
            if triplet in gana_map:
                gana_str += gana_map[triplet]
                i += 3
                continue
        # If not a complete triplet, add the remaining characters
        gana_str += pattern[i:].lower()
        break

    return gana_str


def process_json_files():
    """Process all JSON files and convert to CSV format"""

    base_path = Path('/Users/gauthamkrishna/Projects/chanda/repos/chandas/chandas/svat/data')
    output_path = Path('/Users/gauthamkrishna/Projects/chanda/data')

    json_files = ['curated.json', 'ganesh.json', 'vrttaratnakara.json', 'mishra.json']

    # Categorize meters by type
    sama_meters = []
    ardhasama_meters = []
    vishama_meters = []
    regex_meters = []  # Meters with regex patterns (mostly matra-based)

    total_imported = 0
    skipped = 0

    for json_file in json_files:
        filepath = base_path / json_file
        if not filepath.exists():
            print(f"Warning: {json_file} not found")
            continue

        print(f"\nProcessing {json_file}...")

        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        if 'metres' not in data:
            print(f"  No 'metres' key in {json_file}")
            continue

        for name, pattern_data in data['metres']:
            # Skip TODO entries
            if isinstance(pattern_data, str) and pattern_data.startswith('TODO'):
                skipped += 1
                continue

            # Extract pattern from different formats
            pattern = None

            if isinstance(pattern_data, str):
                # Simple string pattern
                pattern = clean_pattern(pattern_data)
            elif isinstance(pattern_data, dict):
                # Dictionary with 'pattern' or 'regex' key
                if 'pattern' in pattern_data:
                    pattern = clean_pattern(pattern_data['pattern'])
                elif 'regex' in pattern_data:
                    # Skip regex-based patterns for now (need special handling)
                    regex_meters.append((name, pattern_data['regex'], json_file))
                    skipped += 1
                    continue
            elif isinstance(pattern_data, list):
                # List of patterns (ardhasama or vishama)
                if len(pattern_data) == 2:
                    # Ardhasama (odd/even pada patterns)
                    odd_pattern = clean_pattern(pattern_data[0])
                    even_pattern = clean_pattern(pattern_data[1])
                    if odd_pattern and even_pattern:
                        ardhasama_meters.append({
                            'name': name,
                            'odd_pattern': odd_pattern,
                            'even_pattern': even_pattern,
                            'source': json_file
                        })
                        total_imported += 1
                    else:
                        skipped += 1
                    continue
                elif len(pattern_data) == 4:
                    # Vishama (4 different pada patterns)
                    patterns = [clean_pattern(p) for p in pattern_data]
                    if all(patterns):
                        vishama_meters.append({
                            'name': name,
                            'pada1': patterns[0],
                            'pada2': patterns[1],
                            'pada3': patterns[2],
                            'pada4': patterns[3],
                            'source': json_file
                        })
                        total_imported += 1
                    else:
                        skipped += 1
                    continue

            # Process sama-vrtta meters
            if pattern and re.match(r'^[LG]+$', pattern):
                gana = convert_to_gana_notation(pattern)
                syllables = calculate_syllables(pattern)
                matra = calculate_matra(pattern)

                sama_meters.append({
                    'name': name,
                    'gana': gana,
                    'pattern': pattern.lower(),
                    'syllables': syllables,
                    'matra': matra,
                    'source': json_file
                })
                total_imported += 1
            elif pattern:
                # Non-standard pattern
                skipped += 1
                print(f"  Skipped {name}: non-standard pattern '{pattern}'")
            else:
                skipped += 1

    print("\n=== Import Summary ===")
    print(f"Total meters imported: {total_imported}")
    print(f"  Sama-vrtta: {len(sama_meters)}")
    print(f"  Ardhasama-vrtta: {len(ardhasama_meters)}")
    print(f"  Vishama-vrtta: {len(vishama_meters)}")
    print(f"Skipped: {skipped} (regex-based or invalid patterns)")
    print(f"Regex meters (for future processing): {len(regex_meters)}")

    # Write to CSV files
    print("\n=== Writing CSV files ===")

    # Write sama meters to new file (we'll merge with existing later)
    sama_output = output_path / 'chanda_sama_imported.csv'
    with open(sama_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        # Match our existing format: वृत्त,पद,लक्षण,लक्षण (raw),अक्षरसङ्ख्या,मात्रा,यति
        writer.writerow(['वृत्त', 'पद', 'लक्षण', 'लक्षण (raw)', 'अक्षरसङ्ख्या', 'मात्रा', 'यति'])
        for meter in sorted(sama_meters, key=lambda x: x['name']):
            writer.writerow([
                meter['name'],
                '',  # पद (empty)
                meter['gana'],
                meter['pattern'],
                meter['syllables'],
                meter['matra'],
                ''  # यति (empty)
            ])
    print(f"Written {len(sama_meters)} sama meters to {sama_output}")

    # Write ardhasama meters
    ardhasama_output = output_path / 'chanda_ardhasama_imported.csv'
    with open(ardhasama_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['वृत्त', 'विषम-पद', 'सम-पद', 'अक्षरसङ्ख्या', 'source'])
        for meter in sorted(ardhasama_meters, key=lambda x: x['name']):
            odd_syllables = calculate_syllables(meter['odd_pattern'])
            even_syllables = calculate_syllables(meter['even_pattern'])
            total_syllables = (odd_syllables + even_syllables) * 2
            writer.writerow([
                meter['name'],
                meter['odd_pattern'].lower(),
                meter['even_pattern'].lower(),
                total_syllables,
                meter['source']
            ])
    print(f"Written {len(ardhasama_meters)} ardhasama meters to {ardhasama_output}")

    # Write vishama meters
    vishama_output = output_path / 'chanda_vishama_imported.csv'
    with open(vishama_output, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['वृत्त', 'पद-1', 'पद-2', 'पद-3', 'पद-4', 'अक्षरसङ्ख्या', 'source'])
        for meter in sorted(vishama_meters, key=lambda x: x['name']):
            total_syllables = sum([
                calculate_syllables(meter['pada1']),
                calculate_syllables(meter['pada2']),
                calculate_syllables(meter['pada3']),
                calculate_syllables(meter['pada4'])
            ])
            writer.writerow([
                meter['name'],
                meter['pada1'].lower(),
                meter['pada2'].lower(),
                meter['pada3'].lower(),
                meter['pada4'].lower(),
                total_syllables,
                meter['source']
            ])
    print(f"Written {len(vishama_meters)} vishama meters to {vishama_output}")

    # Save regex meters info for manual review
    regex_output = output_path / 'regex_meters_for_review.txt'
    with open(regex_output, 'w', encoding='utf-8') as f:
        f.write("Regex-based meters (mostly matra-based, need special handling):\n\n")
        for name, regex, source in regex_meters:
            f.write(f"{name} (from {source}):\n")
            f.write(f"  {regex}\n\n")
    print(f"Written {len(regex_meters)} regex meters info to {regex_output}")

    return sama_meters, ardhasama_meters, vishama_meters, regex_meters


if __name__ == '__main__':
    print("=" * 70)
    print("Importing Meter Data from sanskrit-coders/chandas Repository")
    print("=" * 70)

    sama, ardhasama, vishama, regex = process_json_files()

    print("\n" + "=" * 70)
    print("Import Complete!")
    print("=" * 70)
    print("\nNext steps:")
    print("1. Review the imported CSV files")
    print("2. Merge with existing data (handling duplicates)")
    print("3. Test with test_all_fixes.py to measure improvement")
