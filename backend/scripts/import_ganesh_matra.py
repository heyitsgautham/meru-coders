#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Import Mātrā meters from ganesh.json

This script parses the authoritative mātrā meter definitions from
Dr. R. Ganesh's curated list and adds them to our chanda_matra.csv.

The mātrā notation in ganesh.json:
- Numbers represent groups of 2-mātrā syllables (e.g., "22" = two 2-mātrā syllables)
- "4" represents a 4-mātrā group (laghu-guru or guru-laghu or four laghus)
- "L" represents a single laghu (1 mātrā)
- "121" represents patterns like laghu-guru-laghu
- "." represents caesura/yati

Example: Āryā ["22 4 22", "4 22 121 22 ."]
- Pada 1: 22 4 22 = (2+2) + 4 + (2+2) = 12 mātrās
- Pada 2: 4 22 121 22 . = 4 + (2+2) + (1+2+1) + (2+2) = 18 mātrās
- Pada 3: 22 4 22 = 12 mātrās
- Pada 4: 4 22 1 22 . = 4 + (2+2) + 1 + (2+2) = 15 mātrās
Total: 12-18-12-15 mātrās

Reference: Shatavadhani Dr. R. Ganesh
YouTube: https://www.youtube.com/playlist?list=PLABJEFgj0PWVXr2ERGu2xtoSXrNdBs5xS
"""

import csv
import json
from collections import OrderedDict

from backend.config import settings


def parse_matra_pattern(pattern_str):
    """
    Parse a mātrā pattern string into total mātrā count.

    Pattern notation from ganesh.json:
    - "22" means: two 2-mātrā groups = 2+2 = 4 mātrās
    - "4" means: one 4-mātrā group = 4 mātrās
    - "121" means: 1+2+1 = 4 mātrās (each digit is independent)
    - "22 4 22" means: (2+2) + 4 + (2+2) = 12 mātrās
    - "L" = 1 mātrā (laghu)
    - "2L" = 2+1 = 3 mātrās
    - Spaces separate groups for clarity but don't affect counting
    """
    # Remove dashes, dots (caesura markers) but keep spaces initially
    clean = pattern_str.replace('—', '').replace('-', '').replace('.', '')

    # Handle special patterns
    if '|' in clean or '(' in clean:
        # Variant patterns - take first option
        clean = clean.split('|')[0].replace('(', '').replace(')', '')

    # Now remove spaces for counting
    clean = clean.replace(' ', '')

    total = 0
    i = 0
    while i < len(clean):
        if clean[i] == 'L':
            total += 1
            i += 1
        elif clean[i].isdigit():
            # Each digit represents its mātrā value
            # "22" = 2 + 2 = 4 (not "22" as a number)
            # "121" = 1 + 2 + 1 = 4
            total += int(clean[i])
            i += 1
        else:
            i += 1

    return total


def parse_matra_meter(meter_data):
    """
    Parse a meter entry and extract mātrā information.

    Returns:
    - name: Meter name
    - matra_sequence: String of mātrā counts per pada (e.g., "12181215")
    - regex_patterns: List of regex patterns for matching
    - comment: Description
    - examples: Example verses
    - video: YouTube video ID if available
    """
    name = meter_data[0]

    # Extract name variants (handle parentheses)
    # e.g., "Anuṣṭup (Śloka)" -> main name is Anuṣṭup
    name = name.split('(')[0].strip()

    if isinstance(meter_data[1], str):
        # Simple pattern string - not a mātrā meter
        return None

    if not isinstance(meter_data[1], dict):
        return None

    meter_info = meter_data[1]

    # Check if this is a mātrā meter (has 'regex' field)
    if 'regex' not in meter_info:
        return None

    regex_patterns = meter_info['regex']
    if regex_patterns == "TODO01":
        # Anuṣṭup - not a simple mātrā meter
        return None

    # IMPORTANT: Extract mātrā counts from the COMMENT field
    # The regex patterns are symbolic and complex
    # The comment has the authoritative mātrā counts
    comment = meter_info.get('comment', '')

    # Parse comment like "The four pādas have 12, 18, 12, and 15 mātrās respectively."
    pada_matras = []
    if 'pādas have' in comment or 'padas have' in comment:
        # Extract numbers from comment
        import re

        numbers = re.findall(r'\d+', comment)
        if numbers:
            pada_matras = [int(n) for n in numbers]

    # If we couldn't parse from comment, try parsing patterns (fallback)
    if not pada_matras:
        if isinstance(regex_patterns, str):
            regex_patterns = [regex_patterns]

        for pattern in regex_patterns:
            if pattern.strip():
                matra_count = parse_matra_pattern(pattern)
                if matra_count > 0:
                    pada_matras.append(matra_count)

    if not pada_matras:
        return None

    # Create the mātrā sequence string
    matra_sequence = ''.join(str(m) for m in pada_matras)

    return {
        'name': name,
        'matra_sequence': matra_sequence,
        'pada_matras': pada_matras,
        'regex_patterns': regex_patterns if isinstance(regex_patterns, list) else [regex_patterns],
        'comment': comment,
        'examples': meter_info.get('examples', []),
        'video': meter_info.get('video', ''),
    }


def load_existing_matra_meters(csv_file):
    """Load existing mātrā meters from CSV."""
    existing = {}
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row and len(row) >= 2:
                    name = row[0].strip()
                    matra = row[1].strip()
                    existing[name] = matra
    except FileNotFoundError:
        pass
    return existing


def main():
    # Load ganesh.json
    ganesh_file = 'repos/sanskrit/data/ganesh.json'
    with open(ganesh_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Parse mātrā meters
    matra_meters = []
    other_info = {}

    print("Parsing mātrā meters from ganesh.json...")
    for meter_entry in data['metres']:
        result = parse_matra_meter(meter_entry)
        if result:
            matra_meters.append(result)
            print(f"  ✓ {result['name']}: {'-'.join(str(m) for m in result['pada_matras'])} mātrās")
            if result['comment']:
                print(f"    Comment: {result['comment']}")
            if result['video']:
                print(f"    Video: {result['video']}")

            # Store additional info for examples.json
            other_info[result['name']] = {
                'comment': result['comment'],
                'examples': result['examples'],
                'video': result['video'],
            }

    print(f"\nFound {len(matra_meters)} mātrā meters")

    # Load existing mātrā meters
    csv_file = settings.DATA_DIR / 'chanda_matra.csv'
    existing = load_existing_matra_meters(csv_file)
    print(f"\nExisting mātrā meters: {len(existing)}")

    # Merge - keep existing, add new ones
    merged = OrderedDict()

    # First add existing (to preserve order)
    for name, matra in existing.items():
        merged[name] = matra
        print(f"  Existing: {name} -> {matra}")

    # Add new ones (check for duplicates)
    new_count = 0
    for meter in matra_meters:
        name = meter['name']
        matra_seq = meter['matra_sequence']

        if name not in merged:
            merged[name] = matra_seq
            new_count += 1
            print(f"  NEW: {name} -> {matra_seq}")
        else:
            # Check if definition matches
            if merged[name] != matra_seq:
                print(f"  ⚠ CONFLICT: {name}")
                print(f"    Existing: {merged[name]}")
                print(f"    Ganesh: {matra_seq}")
                print("    Keeping existing definition")

    print(f"\nTotal merged: {len(merged)} ({new_count} new)")

    # Write updated CSV
    backup_file = csv_file + '.backup'
    import os
    import shutil

    if os.path.exists(csv_file):
        shutil.copy(csv_file, backup_file)
        print(f"\nBackup created: {backup_file}")

    with open(csv_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['वृत्त', 'मात्रा'])
        for name, matra in merged.items():
            writer.writerow([name, matra])

    print(f"\nUpdated {csv_file}")

    # Update examples.json if needed
    examples_file = settings.DATA_DIR / 'examples.json'
    try:
        with open(examples_file, 'r', encoding='utf-8') as f:
            examples = json.load(f)
    except FileNotFoundError:
        examples = {}

    # Add new examples and metadata
    updated_examples = False
    for name, info in other_info.items():
        if info['examples'] and name not in examples:
            examples[name] = {
                'description': info['comment'],
                'examples': info['examples'],
                'video': info['video'] if info['video'] else None,
            }
            updated_examples = True
            print(f"  Added examples for: {name}")

    if updated_examples:
        with open(examples_file, 'w', encoding='utf-8', newline='\n') as f:
            json.dump(examples, f, ensure_ascii=False, indent=2)
        print(f"\nUpdated {examples_file}")

    print("\n✓ Import complete!")
    print("\nSummary:")
    print(f"  - Total mātrā meters: {len(merged)}")
    print(f"  - New meters added: {new_count}")
    print(f"  - Examples added: {sum(1 for i in other_info.values() if i['examples'])}")


if __name__ == '__main__':
    main()
