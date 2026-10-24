#!/usr/bin/env python3
"""
Script to merge matching_chandas.csv and match_chandas.csv into a single clean CSV.
Automatically detects and normalizes column names.
"""

import csv
import os
import re
from pathlib import Path

# Paths
DATA_DIR = Path(__file__).parent.parent / "data"
SOURCE_DIR = Path(__file__).parent.parent / "source"

FILE1 = DATA_DIR / "matching_chandas.csv"
FILE2 = DATA_DIR / "match_chandas.csv"
OUTPUT_FILE = SOURCE_DIR / "merged_chandas_verses.csv"


def normalize_column_name(col: str) -> str:
    """Normalize column name to detect sloka/verse and chanda columns."""
    col_lower = col.lower().strip()
    # Remove extra spaces
    col_lower = re.sub(r'\s+', ' ', col_lower)
    return col_lower


def detect_columns(headers: list) -> dict:
    """
    Detect which columns correspond to sloka/verse and chanda.
    Returns a mapping: {'verse': col_name, 'chanda': col_name, 'extra': [other cols]}
    """
    normalized = {normalize_column_name(h): h for h in headers}

    mapping = {'verse': None, 'chanda': None, 'extra': []}

    # Patterns to detect verse/sloka columns - prioritize 'full' variants
    verse_patterns = ['full_verse', 'full verse', 'full  verse', 'sloka', 'shloka', 'text']
    # Only use 'verse' alone as a last resort (lower priority)
    verse_fallback = ['verse']
    chanda_patterns = ['chandas', 'chanda', 'meter', 'metre']
    # chandaiast is IAST transliteration, not the primary chanda column

    for norm_name, orig_name in normalized.items():
        matched = False
        for pattern in verse_patterns:
            if pattern == norm_name or (pattern in norm_name and 'full' in norm_name):
                if mapping['verse'] is None:
                    mapping['verse'] = orig_name
                    matched = True
                    break

        if not matched:
            for pattern in chanda_patterns:
                if pattern == norm_name:
                    if mapping['chanda'] is None:
                        mapping['chanda'] = orig_name
                        matched = True
                        break

        if not matched and orig_name.strip():
            mapping['extra'].append(orig_name)

    # If no verse column found, try fallback patterns
    if mapping['verse'] is None:
        for norm_name, orig_name in normalized.items():
            for pattern in verse_fallback:
                if pattern == norm_name:
                    mapping['verse'] = orig_name
                    break
            if mapping['verse']:
                break

    return mapping


def clean_verse(verse: str) -> str:
    """Clean verse text - normalize newlines and whitespace."""
    if not verse:
        return ""
    # Replace multiple newlines with single space, then clean up
    verse = verse.replace('\r\n', ' ').replace('\n', ' ').replace('\r', ' ')
    # Normalize multiple spaces
    verse = re.sub(r'\s+', ' ', verse)
    return verse.strip()


def clean_chanda(chanda: str) -> str:
    """Clean and normalize chanda name."""
    if not chanda:
        return ""
    return chanda.strip()


def read_csv_file(filepath: Path) -> list:
    """Read CSV file and return list of (verse, chanda) tuples."""
    records = []

    with open(filepath, 'r', encoding='utf-8') as f:
        # Try to detect delimiter
        sample = f.read(2048)
        f.seek(0)

        try:
            dialect = csv.Sniffer().sniff(sample)
        except csv.Error:
            dialect = csv.excel

        reader = csv.DictReader(f, dialect=dialect)
        headers = reader.fieldnames

        if not headers:
            print(f"  Warning: No headers found in {filepath.name}")
            return records

        # Clean headers (remove empty ones)
        headers = [h for h in headers if h and h.strip()]

        print(f"  Headers detected: {headers}")

        mapping = detect_columns(headers)
        print(f"  Column mapping: verse='{mapping['verse']}', chanda='{mapping['chanda']}'")

        if not mapping['verse'] or not mapping['chanda']:
            print("  Warning: Could not detect verse or chanda columns!")
            return records

        for row in reader:
            verse = row.get(mapping['verse'], '')
            chanda = row.get(mapping['chanda'], '')

            verse = clean_verse(verse)
            chanda = clean_chanda(chanda)

            if verse and chanda:
                records.append((verse, chanda))

    return records


def main():
    print("=" * 60)
    print("Merging Chandas CSV Files")
    print("=" * 60)

    all_records = []

    # Read first file
    print(f"\nReading: {FILE1.name}")
    records1 = read_csv_file(FILE1)
    print(f"  Records loaded: {len(records1)}")
    all_records.extend(records1)

    # Read second file
    print(f"\nReading: {FILE2.name}")
    records2 = read_csv_file(FILE2)
    print(f"  Records loaded: {len(records2)}")
    all_records.extend(records2)

    # Remove duplicates based on verse text
    seen_verses = set()
    unique_records = []
    duplicates = 0

    for verse, chanda in all_records:
        # Create a normalized key for deduplication
        key = verse.lower().replace(' ', '')
        if key not in seen_verses:
            seen_verses.add(key)
            unique_records.append((verse, chanda))
        else:
            duplicates += 1

    print(f"\nTotal records before dedup: {len(all_records)}")
    print(f"Duplicates removed: {duplicates}")
    print(f"Unique records: {len(unique_records)}")

    # Write output
    print(f"\nWriting to: {OUTPUT_FILE}")
    os.makedirs(SOURCE_DIR, exist_ok=True)

    with open(OUTPUT_FILE, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, quoting=csv.QUOTE_MINIMAL)
        # Standard schema
        writer.writerow(['sloka', 'chanda'])

        for verse, chanda in unique_records:
            writer.writerow([verse, chanda])

    print(f"Successfully wrote {len(unique_records)} records to {OUTPUT_FILE.name}")
    print("=" * 60)


if __name__ == "__main__":
    main()
