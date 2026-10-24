#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build dataset with COMPLETE verses only (those with ॥ marker).
"""

import json
import os


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Load Rigveda data
    rigveda_path = os.path.join(base_dir, 'repos/Rigveda_api/data/rigveda.json')
    with open(rigveda_path, 'r') as f:
        rigveda_data = json.load(f)

    print(f"Loaded {len(rigveda_data)} entries from Rigveda_api")

    # Load Anukramani meter annotations
    # Format: hymn.verses.seer.divinity.meter (dot-separated)
    anukramani_dir = os.path.join(base_dir, 'repos/WSC2023/Anukramani')
    meter_map = {}  # key: "mandala.hymn" -> meter

    for filename in os.listdir(anukramani_dir):
        if filename.endswith('.txt'):
            # Extract mandala number from filename (e.g., Mandala_1.txt -> 1)
            mandala = filename.replace('Mandala_', '').replace('.txt', '')
            try:
                mandala = int(mandala)
            except ValueError:
                continue

            filepath = os.path.join(anukramani_dir, filename)
            with open(filepath, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('hymn.'):  # Skip header
                        continue

                    # Format: hymn.verses.seer.divinity.meter
                    parts = line.split('.')
                    if len(parts) >= 5:
                        try:
                            hymn = int(parts[0])
                            meter = parts[-1].lower().strip()

                            # Handle complex meter specs like "(1-7)gāyatrī,(8-9)anuṣṭup"
                            # Just take the first/main meter
                            if ',' in meter:
                                meter = meter.split(',')[0]
                            if ')' in meter:
                                meter = meter.split(')')[-1]

                            # Store as mandala.hymn -> meter
                            key = f"{mandala}.{hymn}"
                            meter_map[key] = meter
                        except (ValueError, IndexError):
                            continue

    print(f"Loaded {len(meter_map)} hymn-level meter annotations from Anukramani")
    print(f"Sample entries: {list(meter_map.items())[:5]}")

    # Filter to only COMPLETE verses (with ॥)
    complete_verses = []
    for v in rigveda_data:
        text = v.get('sanskrit', '')
        if '॥' in text:  # Has verse-end marker = complete verse
            mandala = v['mandala']
            hymn = v['hymn']
            verse = v['verse']
            ref = f"{mandala}.{hymn}.{verse}"

            # Try to find meter from Anukramani (hymn-level)
            hymn_key = f"{mandala}.{hymn}"
            meter = meter_map.get(hymn_key)

            if meter:
                complete_verses.append({
                    'ref': ref,
                    'text': text,
                    'meter': meter,
                    'mandala': mandala,
                    'hymn': hymn,
                    'verse': verse
                })

    print(f"Found {len(complete_verses)} complete verses with meter annotations")

    # Show meter distribution
    meter_dist = {}
    for v in complete_verses:
        m = v['meter']
        meter_dist[m] = meter_dist.get(m, 0) + 1

    print("\nMeter distribution:")
    for m, c in sorted(meter_dist.items(), key=lambda x: -x[1]):
        print(f"  {m}: {c}")

    # Generate Python file
    output_lines = [
        '#!/usr/bin/env python3',
        '# -*- coding: utf-8 -*-',
        '"""',
        'AUTHENTIC Rigveda Test Verses - COMPLETE VERSES ONLY',
        '',
        'Filtered to include only verses with ॥ (verse-end marker).',
        'These are complete verses, not partial padas.',
        '',
        'Sources:',
        '- Verse texts: repos/Rigveda_api/data/rigveda.json (filtered for ॥)',
        '- Meter annotations: repos/WSC2023/Anukramani/',
        '',
        'Generated: 2024-12-02',
        '"""',
        '',
        '# Meter name mappings',
        'METER_DEVANAGARI = {',
        "    'gāyatrī': 'गायत्री',",
        "    'triṣṭup': 'त्रिष्टुभ्',",
        "    'jagatī': 'जगती',",
        "    'anuṣṭup': 'अनुष्टुभ्',",
        "    'bṛhatī': 'बृहती',",
        "    'uṣṇik': 'उष्णिक्',",
        "    'paṅkti': 'पङ्क्ति',",
        '}',
        '',
        '# Expected syllable counts',
        'METER_SYLLABLES = {',
        "    'gāyatrī': 24,",
        "    'triṣṭup': 44,",
        "    'jagatī': 48,",
        "    'anuṣṭup': 32,",
        "    'bṛhatī': 36,",
        "    'uṣṇik': 28,",
        "    'paṅkti': 40,",
        '}',
        '',
        'RIGVEDA_COMPLETE = [',
    ]

    for v in complete_verses:
        text_escaped = v['text'].replace("'", "\\'")
        output_lines.append('    {')
        output_lines.append(f"        'ref': '{v['ref']}',")
        output_lines.append(f"        'text': '{text_escaped}',")
        output_lines.append(f"        'meter': '{v['meter']}',")
        output_lines.append(f"        'meter_devanagari': METER_DEVANAGARI.get('{v['meter']}', '{v['meter']}'),")
        output_lines.append(f"        'expected_syllables': METER_SYLLABLES.get('{v['meter']}', 0),")
        output_lines.append('    },')

    output_lines.append(']')
    output_lines.append('')
    output_lines.append('# Total count')
    output_lines.append('TOTAL_VERSES = len(RIGVEDA_COMPLETE)')
    output_lines.append('')

    # Write to file
    output_path = os.path.join(base_dir, 'backend/evaluation/data/rigveda_complete.py')
    with open(output_path, 'w') as f:
        f.write('\n'.join(output_lines))

    print(f"\nWritten to {output_path}")
    print(f"Total complete verses: {len(complete_verses)}")


if __name__ == '__main__':
    main()
