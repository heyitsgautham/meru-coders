#!/usr/bin/env python3
"""
CSV to Supabase Migration Script
Migrates 11,760+ records from backend/source/*.csv to Supabase PostgreSQL

Usage:
    python backend/scripts/migrate_csv_to_supabase.py
"""

import csv
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from supabase import Client, create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_SERVICE_KEY = os.getenv('SUPABASE_SERVICE_KEY')  # Service role key for admin operations

if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_KEY in environment variables")
    sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# CSV file mappings
SOURCE_DIR = Path(__file__).parent.parent / 'source'
BATCH_SIZE = 100  # Insert records in batches for performance

# ================================================
# MIGRATION FUNCTIONS
# ================================================


def migrate_rigveda():
    """Migrate rigveda-with-meters.csv to verses table"""
    csv_path = SOURCE_DIR / 'rigveda-with-meters.csv'
    if not csv_path.exists():
        print(f"⚠️  WARNING: {csv_path} not found, skipping...")
        return 0

    print(f"\n📖 Migrating Rigveda verses from {csv_path}...")

    verses = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            verse = {
                'verse_text': row.get('verse_text', ''),
                'meter': row.get('meter', ''),
                'lg_pattern': row.get('lg_pattern'),
                'syllable_count': int(row['syllable_count'])
                if row.get('syllable_count') and row['syllable_count'].isdigit()
                else None,
                'source': 'rigveda',
                'metadata': {
                    'mandala': row.get('mandala'),
                    'sukta': row.get('sukta'),
                    'rik': row.get('rik'),
                    'seer': row.get('seer'),
                    'divinity': row.get('divinity'),
                },
                'is_approved': True,
                'contributed_by': None,
            }
            verses.append(verse)

    # Insert in batches
    total = len(verses)
    for i in range(0, total, BATCH_SIZE):
        batch = verses[i : i + BATCH_SIZE]
        supabase.table('verses').insert(batch).execute()
        print(f"  ✓ Inserted {min(i + BATCH_SIZE, total)}/{total} verses")

    print(f"✅ Rigveda migration complete: {total} verses")
    return total


def migrate_chandovallari():
    """Migrate chandovallari.csv to verses table"""
    csv_path = SOURCE_DIR / 'chandovallari.csv'
    if not csv_path.exists():
        print(f"⚠️  WARNING: {csv_path} not found, skipping...")
        return 0

    print(f"\n📖 Migrating Chandovallari verses from {csv_path}...")

    verses = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Chandovallari has columns: Shloka, L/G, Gana, chanda
            verse_text = row.get('Shloka ', row.get('Shloka', row.get('verse_text', '')))
            meter = row.get('chanda', row.get('meter', ''))
            lg_pattern = row.get('L/G', row.get('lg_pattern'))

            verse = {
                'verse_text': verse_text.strip() if verse_text else '',
                'meter': meter.strip() if meter else '',
                'lg_pattern': lg_pattern,
                'syllable_count': None,  # Not provided in chandovallari
                'source': 'chandovallari',
                'metadata': {k: v for k, v in row.items() if v},
                'is_approved': True,
                'contributed_by': None,
            }

            if verse['verse_text']:  # Only add if has text
                verses.append(verse)

    total = len(verses)
    for i in range(0, total, BATCH_SIZE):
        batch = verses[i : i + BATCH_SIZE]
        supabase.table('verses').insert(batch).execute()
        print(f"  ✓ Inserted {min(i + BATCH_SIZE, total)}/{total} verses")

    print(f"✅ Chandovallari migration complete: {total} verses")
    return total


def migrate_chandas_vedanga():
    """Migrate chandas-as-vedanga.csv to verses table"""
    csv_path = SOURCE_DIR / 'chandas-as-vedanga.csv'
    if not csv_path.exists():
        print(f"⚠️  WARNING: {csv_path} not found, skipping...")
        return 0

    print(f"\n📖 Migrating Chandas Vedanga verses from {csv_path}...")

    verses = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # chandas-as-vedanga has: S.No., chandas_class, chandas_name, syllables, examples
            examples = row.get('examples', '')
            if not examples or not examples.strip():
                continue  # Skip entries without example verses

            verse = {
                'verse_text': examples.strip(),
                'meter': row.get('chandas_name', ''),
                'lg_pattern': None,
                'syllable_count': int(row['syllables'])
                if row.get('syllables') and str(row['syllables']).isdigit()
                else None,
                'source': 'vedanga',
                'metadata': {'chandas_class': row.get('chandas_class'), 's_no': row.get('S.No.')},
                'is_approved': True,
                'contributed_by': None,
            }
            verses.append(verse)

    total = len(verses)
    for i in range(0, total, BATCH_SIZE):
        batch = verses[i : i + BATCH_SIZE]
        supabase.table('verses').insert(batch).execute()
        print(f"  ✓ Inserted {min(i + BATCH_SIZE, total)}/{total} verses")

    print(f"✅ Chandas Vedanga migration complete: {total} verses")
    return total


def migrate_meter_definitions(category: str, filename: str):
    """Generic function to migrate meter definition CSVs"""
    csv_path = SOURCE_DIR / filename
    if not csv_path.exists():
        print(f"⚠️  WARNING: {csv_path} not found, skipping...")
        return 0

    print(f"\n📐 Migrating {category} meter definitions from {csv_path}...")

    meters = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # IITK CSVs have columns: वृत्त, पद, लक्षण, लक्षण (raw), अक्षरसङ्ख्या, मात्रा, यति
            meter_name = row.get('वृत्त', row.get('meter_name', row.get('name', '')))
            if not meter_name or not meter_name.strip():
                continue  # Skip empty rows

            meter = {
                'meter_name_devanagari': meter_name.strip(),
                'meter_name_iast': None,
                'category': category,
                'lg_pattern': row.get('लक्षण (raw)', row.get('lg_pattern')),
                'syllable_count': None,
                'matra_count': row.get('मात्रा'),
                'pada_number': None,
                'yati': row.get('यति'),
                'gana': row.get('लक्षण'),  # Gana representation
                'metadata': {k: v for k, v in row.items() if v},
                'is_approved': True,
                'contributed_by': None,
            }

            # Extract syllable count
            if row.get('अक्षरसङ्ख्या'):
                try:
                    meter['syllable_count'] = int(row['अक्षरसङ्ख्या'])
                except Exception:
                    pass

            # Extract pada number
            if row.get('पद'):
                try:
                    meter['pada_number'] = int(row['पद'])
                except Exception:
                    pass

            meters.append(meter)

    total = len(meters)
    if total == 0:
        print(f"⚠️  No meters found in {filename}")
        return 0

    for i in range(0, total, BATCH_SIZE):
        batch = meters[i : i + BATCH_SIZE]
        supabase.table('meter_definitions').insert(batch).execute()
        print(f"  ✓ Inserted {min(i + BATCH_SIZE, total)}/{total} meters")

    print(f"✅ {category.title()} migration complete: {total} meters")
    return total


def verify_migration():
    """Verify that data was migrated successfully"""
    print("\n🔍 Verifying migration...")

    # Count verses
    verses_response = supabase.table('verses').select('id', count='exact').execute()
    verses_count = verses_response.count if hasattr(verses_response, 'count') else len(verses_response.data)

    # Count meter definitions
    meters_response = supabase.table('meter_definitions').select('id', count='exact').execute()
    meters_count = meters_response.count if hasattr(meters_response, 'count') else len(meters_response.data)

    print("\n📊 Migration Summary:")
    print(f"  Total Verses: {verses_count}")
    print(f"  Total Meter Definitions: {meters_count}")
    print(f"  Grand Total: {verses_count + meters_count}")

    # Sample data check
    print("\n📋 Sample Verses:")
    sample_verses = supabase.table('verses').select('*').limit(3).execute()
    for i, verse in enumerate(sample_verses.data, 1):
        print(f"  {i}. {verse['meter']} - {verse['verse_text'][:50]}...")

    print("\n📋 Sample Meter Definitions:")
    sample_meters = supabase.table('meter_definitions').select('*').limit(3).execute()
    for i, meter in enumerate(sample_meters.data, 1):
        print(f"  {i}. {meter['meter_name_devanagari']} ({meter['category']})")


def main():
    """Main migration function"""
    print("=" * 60)
    print("🚀 CSV to Supabase Migration Script")
    print("=" * 60)
    print(f"Source Directory: {SOURCE_DIR}")
    print(f"Supabase URL: {SUPABASE_URL}")
    print(f"Batch Size: {BATCH_SIZE}")
    print("=" * 60)

    total_migrated = 0

    try:
        # Migrate verses
        total_migrated += migrate_rigveda()
        total_migrated += migrate_chandovallari()
        total_migrated += migrate_chandas_vedanga()

        # Migrate meter definitions
        meter_files = [
            ('sama', 'chanda_sama-iitk.csv'),
            ('vishama', 'chanda_vishama-iitk.csv'),
            ('ardhasama', 'chanda_ardhasama-iitk.csv'),
            ('matra', 'chanda_matra-iitk.csv'),
            ('jaati', 'chanda_jaati-iitk.csv'),
        ]

        for category, filename in meter_files:
            total_migrated += migrate_meter_definitions(category, filename)

        # Verify migration
        verify_migration()

        print("\n" + "=" * 60)
        print(f"✅ MIGRATION COMPLETE: {total_migrated} records migrated")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ ERROR during migration: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
