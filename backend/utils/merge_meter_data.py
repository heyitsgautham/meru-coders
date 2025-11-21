#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge imported meter data with existing data, handling duplicates intelligently

Strategy:
1. Load existing data (348 sama, 16 ardhasama, 36 vishama)
2. Load imported data (1338 sama, 154 ardhasama, 41 vishama)
3. Merge with duplicate detection based on patterns
4. Create backup of original files
5. Write merged data
"""

import csv
import shutil
from pathlib import Path
from datetime import datetime
from collections import defaultdict


def load_csv_data(filepath):
    """Load CSV data into a list of dictionaries"""
    data = []
    with open(filepath, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data


def normalize_pattern(pattern):
    """Normalize pattern for comparison"""
    if not pattern:
        return ''
    return pattern.lower().replace(' ', '').replace('–', '').replace('—', '')


def merge_sama_data(original_file, imported_file, output_file):
    """Merge sama-vrtta data"""
    print("\n=== Merging Sama-vrtta Data ===")
    
    original = load_csv_data(original_file)
    imported = load_csv_data(imported_file)
    
    # Track patterns to detect duplicates
    pattern_to_names = defaultdict(list)
    
    # First, index original data by pattern
    for row in original:
        pattern = normalize_pattern(row.get('लक्षण (raw)', ''))
        if pattern:
            pattern_to_names[pattern].append({
                'name': row.get('वृत्त', ''),
                'source': 'original',
                'row': row
            })
    
    # Check imported data for duplicates
    new_entries = []
    duplicates = []
    pattern_conflicts = []
    
    for row in imported:
        pattern = normalize_pattern(row.get('लक्षण (raw)', ''))
        name = row.get('वृत्त', '')
        
        if pattern and pattern in pattern_to_names:
            # Pattern exists - check if same name
            existing_names = [e['name'] for e in pattern_to_names[pattern]]
            if name in existing_names:
                duplicates.append(name)
            else:
                # Same pattern, different name (meter synonym)
                pattern_conflicts.append({
                    'new_name': name,
                    'existing_names': existing_names,
                    'pattern': pattern
                })
                # Add as new entry (it's a valid synonym)
                new_entries.append(row)
                pattern_to_names[pattern].append({
                    'name': name,
                    'source': 'imported',
                    'row': row
                })
        else:
            # Completely new pattern
            new_entries.append(row)
            if pattern:
                pattern_to_names[pattern].append({
                    'name': name,
                    'source': 'imported',
                    'row': row
                })
    
    print(f"Original entries: {len(original)}")
    print(f"Imported entries: {len(imported)}")
    print(f"New unique patterns: {len(new_entries)}")
    print(f"Exact duplicates skipped: {len(duplicates)}")
    print(f"Pattern conflicts (synonyms): {len(pattern_conflicts)}")
    
    # Write merged data
    merged_data = original + new_entries
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        # Use same headers as original
        fieldnames = ['वृत्त', 'पद', 'लक्षण', 'लक्षण (raw)', 'अक्षरसङ्ख्या', 'मात्रा', 'यति']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged_data)
    
    print(f"Merged data written: {len(merged_data)} entries")
    
    # Write synonym report
    if pattern_conflicts:
        synonym_file = output_file.parent / 'meter_synonyms_report.txt'
        with open(synonym_file, 'w', encoding='utf-8') as f:
            f.write("Meter Synonyms Detected (Same Pattern, Different Names)\n")
            f.write("=" * 70 + "\n\n")
            for conflict in pattern_conflicts[:50]:  # Show first 50
                f.write(f"New: {conflict['new_name']}\n")
                f.write(f"Existing: {', '.join(conflict['existing_names'])}\n")
                f.write(f"Pattern: {conflict['pattern']}\n")
                f.write("-" * 70 + "\n")
        print(f"Synonym report written to {synonym_file}")
    
    return len(merged_data), len(duplicates), len(pattern_conflicts)


def merge_ardhasama_data(original_file, imported_file, output_file):
    """Merge ardhasama-vrtta data"""
    print("\n=== Merging Ardhasama-vrtta Data ===")
    
    original = load_csv_data(original_file)
    imported = load_csv_data(imported_file)
    
    # Create pattern key from odd+even patterns
    def pattern_key(row):
        odd = normalize_pattern(row.get('विषम-पद', ''))
        even = normalize_pattern(row.get('सम-पद', ''))
        return f"{odd}|{even}"
    
    existing_patterns = {pattern_key(row): row.get('वृत्त', '') for row in original}
    
    new_entries = []
    duplicates = 0
    
    for row in imported:
        key = pattern_key(row)
        if key not in existing_patterns:
            new_entries.append(row)
            existing_patterns[key] = row.get('वृत्त', '')
        else:
            duplicates += 1
    
    print(f"Original entries: {len(original)}")
    print(f"Imported entries: {len(imported)}")
    print(f"New entries: {len(new_entries)}")
    print(f"Duplicates skipped: {duplicates}")
    
    # Read original to preserve format
    with open(original_file, 'r', encoding='utf-8') as f:
        original_rows = list(csv.DictReader(f))
    
    # Normalize fieldnames - merge all unique fields
    if original_rows and new_entries:
        all_fields = set()
        for row in original_rows + new_entries:
            all_fields.update(row.keys())
        fieldnames = sorted(list(all_fields))
    elif original_rows:
        fieldnames = list(original_rows[0].keys())
    else:
        fieldnames = list(new_entries[0].keys()) if new_entries else []
    
    merged_data = original_rows + new_entries
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(merged_data)
    
    print(f"Merged data written: {len(merged_data)} entries")
    return len(merged_data), duplicates


def merge_vishama_data(original_file, imported_file, output_file):
    """Merge vishama-vrtta data"""
    print("\n=== Merging Vishama-vrtta Data ===")
    
    original = load_csv_data(original_file)
    imported = load_csv_data(imported_file)
    
    # Create pattern key from all 4 padas
    def pattern_key(row):
        p1 = normalize_pattern(row.get('पद-1', ''))
        p2 = normalize_pattern(row.get('पद-2', ''))
        p3 = normalize_pattern(row.get('पद-3', ''))
        p4 = normalize_pattern(row.get('पद-4', ''))
        return f"{p1}|{p2}|{p3}|{p4}"
    
    existing_patterns = {pattern_key(row): row.get('वृत्त', '') for row in original}
    
    new_entries = []
    duplicates = 0
    
    for row in imported:
        key = pattern_key(row)
        if key not in existing_patterns:
            new_entries.append(row)
            existing_patterns[key] = row.get('वृत्त', '')
        else:
            duplicates += 1
    
    print(f"Original entries: {len(original)}")
    print(f"Imported entries: {len(imported)}")
    print(f"New entries: {len(new_entries)}")
    print(f"Duplicates skipped: {duplicates}")
    
    # Read original to preserve format
    with open(original_file, 'r', encoding='utf-8') as f:
        original_rows = list(csv.DictReader(f))
    
    # Normalize fieldnames - merge all unique fields
    if original_rows and new_entries:
        all_fields = set()
        for row in original_rows + new_entries:
            all_fields.update(row.keys())
        fieldnames = sorted(list(all_fields))
    elif original_rows:
        fieldnames = list(original_rows[0].keys())
    else:
        fieldnames = list(new_entries[0].keys()) if new_entries else []
    
    merged_data = original_rows + new_entries
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(merged_data)
    
    print(f"Merged data written: {len(merged_data)} entries")
    return len(merged_data), duplicates


def main():
    print("=" * 70)
    print("Merging Imported Meter Data with Existing Data")
    print("=" * 70)
    
    data_dir = Path('/Users/gauthamkrishna/Projects/chanda/data')
    
    # Create backups
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_dir = data_dir / f'backup_{timestamp}'
    backup_dir.mkdir(exist_ok=True)
    
    print(f"\nCreating backups in {backup_dir}")
    for file in ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv']:
        src = data_dir / file
        if src.exists():
            shutil.copy2(src, backup_dir / file)
            print(f"  Backed up {file}")
    
    # Merge data
    stats = {}
    
    # Sama
    sama_total, sama_dup, sama_syn = merge_sama_data(
        data_dir / 'chanda_sama.csv',
        data_dir / 'chanda_sama_imported.csv',
        data_dir / 'chanda_sama_merged.csv'
    )
    stats['sama'] = {'total': sama_total, 'duplicates': sama_dup, 'synonyms': sama_syn}
    
    # Ardhasama
    ardha_total, ardha_dup = merge_ardhasama_data(
        data_dir / 'chanda_ardhasama.csv',
        data_dir / 'chanda_ardhasama_imported.csv',
        data_dir / 'chanda_ardhasama_merged.csv'
    )
    stats['ardhasama'] = {'total': ardha_total, 'duplicates': ardha_dup}
    
    # Vishama
    vishama_total, vishama_dup = merge_vishama_data(
        data_dir / 'chanda_vishama.csv',
        data_dir / 'chanda_vishama_imported.csv',
        data_dir / 'chanda_vishama_merged.csv'
    )
    stats['vishama'] = {'total': vishama_total, 'duplicates': vishama_dup}
    
    # Summary
    print("\n" + "=" * 70)
    print("Merge Summary")
    print("=" * 70)
    print(f"\nSama-vrtta: {stats['sama']['total']} entries")
    print(f"  (including {stats['sama']['synonyms']} synonyms)")
    print(f"Ardhasama-vrtta: {stats['ardhasama']['total']} entries")
    print(f"Vishama-vrtta: {stats['vishama']['total']} entries")
    print(f"\nTotal: {sama_total + ardha_total + vishama_total} entries")
    print(f"Original total: 400 entries")
    print(f"Net increase: {sama_total + ardha_total + vishama_total - 400} entries")
    
    print("\n" + "=" * 70)
    print("Next Steps:")
    print("=" * 70)
    print("1. Review merged files: chanda_*_merged.csv")
    print("2. Check meter_synonyms_report.txt for synonym conflicts")
    print("3. If satisfied, replace original files:")
    print("   mv data/chanda_sama_merged.csv data/chanda_sama.csv")
    print("   mv data/chanda_ardhasama_merged.csv data/chanda_ardhasama.csv")
    print("   mv data/chanda_vishama_merged.csv data/chanda_vishama.csv")
    print("4. Run tests: python tests/test_all_fixes.py")


if __name__ == '__main__':
    main()
