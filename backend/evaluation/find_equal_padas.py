#!/usr/bin/env python3
"""Find verses with equal syllables per pada for all 7 Vedic meters."""

import csv

from backend.config import settings
from backend.core.chanda import Chanda

chanda = Chanda(data_path=str(settings.DATA_DIR))

# Target meters with expected syllable counts per pada
targets = {
    'Gayatri': (24, 8, 3),  # 24 total, 8 per pada, 3 padas
    'Ushnik': (28, 7, 4),  # 28 total, 7 per pada, 4 padas
    'Anushtubh': (32, 8, 4),  # 32 total, 8 per pada, 4 padas
    'Brihati': (36, 9, 4),  # 36 total, 9 per pada, 4 padas
    'Pankti': (40, 8, 5),  # 40 total, 8 per pada, 5 padas
    'Trishtubh': (44, 11, 4),  # 44 total, 11 per pada, 4 padas
    'Jagati': (48, 12, 4),  # 48 total, 12 per pada, 4 padas
}

found = {k: [] for k in targets}

print("Searching for verses with equal padas...")
print("=" * 80)

with open(str(settings.DATA_DIR / 'rigveda_with_meters_complete.csv'), 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    header = next(reader)

    for row in reader:
        if len(row) < 7:
            continue
        mandala, sukta, rik, verse, meter, lg_pattern, syllable_count = row[:7]

        try:
            syl_count = int(syllable_count)
        except Exception:
            continue

        for meter_name, (total, _per_pada, _num_padas) in targets.items():
            if syl_count == total and len(found[meter_name]) < 5:
                result = chanda.identify_line(verse)
                if result and 'display_syllables' in result:
                    syllables = result['display_syllables']
                    actual_count = len(syllables)

                    if actual_count == total:
                        found[meter_name].append(
                            {
                                'ref': f'RV {mandala}.{sukta}.{rik}',
                                'verse': verse,
                                'syllables': syllables,
                                'lg': result.get('display_lg', []),
                                'count': actual_count,
                                'meter_detected': result.get('display_chanda_primary', 'Unknown'),
                            }
                        )

# Print results
for meter_name in ['Gayatri', 'Ushnik', 'Anushtubh', 'Brihati', 'Pankti', 'Trishtubh', 'Jagati']:
    verses = found[meter_name]
    total, per_pada, num_padas = targets[meter_name]

    print(f'\n{"=" * 80}')
    print(f'{meter_name.upper()} ({total} = {num_padas} × {per_pada} syllables per pada)')
    print(f'{"=" * 80}')

    if verses:
        v = verses[0]  # Best match
        print(f"\n📜 Source: {v['ref']}")
        print("\n📝 Verse:")
        print(f"   {v['verse']}")
        print(f"\n🔍 Detected as: {v['meter_detected']}")
        print(f"\n🔢 Syllable Breakdown ({v['count']} total):\n")

        syls = v['syllables']
        lg = v['lg']

        for i in range(num_padas):
            start = i * per_pada
            end = (i + 1) * per_pada
            pada_syls = syls[start:end] if start < len(syls) else []
            pada_lg = lg[start:end] if start < len(lg) else []

            syl_str = '-'.join(pada_syls)
            lg_str = ''.join(pada_lg)

            print(f"   Pada {i + 1} ({len(pada_syls)} syl): {syl_str}")
            print(f"           L-G: {lg_str}")
            print()
    else:
        print("   ❌ No exact match found in database")

print("\n" + "=" * 80)
print("SEARCH COMPLETE")
print("=" * 80)
