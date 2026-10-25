#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Consolidate mātrā meters CSV - remove duplicates and fix conflicts

This script:
1. Removes duplicate IAST entries where Sanskrit equivalents exist
2. Uses ganesh.json as authoritative source for conflicts
3. Adds meter name synonyms tracking
"""

import csv

from indic_transliteration import sanscript


def transliterate_to_devanagari(iast_name):
    """Transliterate IAST to Devanagari."""
    try:
        return sanscript.transliterate(iast_name, sanscript.IAST, sanscript.DEVANAGARI)
    except Exception:
        return None


def main():
    input_file = 'data/chanda_matra.csv'
    output_file = 'data/chanda_matra.csv'

    # Read current CSV
    meters = []
    with open(input_file, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader)  # skip the header row
        for row in reader:
            if row and len(row) >= 2:
                meters.append((row[0].strip(), row[1].strip()))

    print(f"Read {len(meters)} meters from CSV\n")

    # First pass: collect all Sanskrit/Devanagari meters
    consolidated = {}  # {devanagari_name: (matra_pattern, [synonyms])}
    iast_meters = []
    conflicts = []

    for name, pattern in meters:
        # Check if this is IAST (Latin script with diacritics) vs Devanagari
        # Devanagari range: U+0900 to U+097F
        is_devanagari = any('\u0900' <= c <= '\u097f' for c in name)

        if not is_devanagari:
            # IAST or other Latin script
            iast_meters.append((name, pattern))
        else:
            # Devanagari name - add directly
            consolidated[name] = (pattern, [])

    # Second pass: process IAST meters
    for name, pattern in iast_meters:
        sanskrit = transliterate_to_devanagari(name)
        if sanskrit:
            if sanskrit in consolidated:
                # Check for conflicts
                existing_pattern = consolidated[sanskrit][0]
                if existing_pattern != pattern:
                    conflicts.append({'name': name, 'sanskrit': sanskrit, 'existing': existing_pattern, 'new': pattern})
                    # Use ganesh.json data (the IAST new one) as authoritative
                    print(f"⚠ CONFLICT: {name} ({sanskrit})")
                    print(f"  Old: {existing_pattern}")
                    print(f"  New: {pattern} <- Using ganesh.json (authoritative)")
                    consolidated[sanskrit] = (pattern, consolidated[sanskrit][1] + [name])
                else:
                    # True duplicate - just add synonym
                    print(f"✓ Duplicate removed: {name} (same as {sanskrit})")
                    consolidated[sanskrit] = (consolidated[sanskrit][0], consolidated[sanskrit][1] + [name])
            else:
                # New meter in IAST form - transliterate and add
                consolidated[sanskrit] = (pattern, [name])
                print(f"→ Transliterated: {name} -> {sanskrit}")
        else:
            # Keep IAST if can't transliterate
            consolidated[name] = (pattern, [])
            print(f"→ Kept IAST: {name} (couldn't transliterate)")

    print(f"\nConsolidated to {len(consolidated)} unique meters")

    # Write consolidated CSV
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['वृत्त', 'मात्रा', 'पर्यायवाचि'])  # Added synonyms column

        for name in sorted(consolidated.keys()):
            pattern, synonyms = consolidated[name]
            synonym_str = ', '.join(synonyms) if synonyms else ''
            writer.writerow([name, pattern, synonym_str])

    print(f"\n✓ Updated {output_file}")

    # Report
    if conflicts:
        print(f"\n⚠ {len(conflicts)} conflicts resolved (used ganesh.json data)")
        for c in conflicts:
            print(f"  - {c['name']}: {c['existing']} -> {c['new']}")

    print(f"\nFinal count: {len(consolidated)} unique mātrā meters")


if __name__ == '__main__':
    main()
