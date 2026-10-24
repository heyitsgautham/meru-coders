#!/usr/bin/env python3
"""Merge original and imported chandas CSVs into the main CSV files.

Creates backups of the original target files before overwriting.
"""

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'backend' / 'data'


def merge_ardhasama():
    orig = ROOT / 'chanda_ardhasama_original.csv'
    imported = ROOT / 'chanda_ardhasama_imported.csv'
    target = ROOT / 'chanda_ardhasama.csv'
    backup = target.with_suffix(target.suffix + '.bak')

    # Read original
    out_rows = []
    with orig.open('r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r in reader:
            out_rows.append(r)

    # Read imported and map into target schema
    with imported.open('r', encoding='utf-8') as f:
        dreader = csv.DictReader(f)
        for row in dreader:
            vrtt = row.get('वृत्त', row.get('vrtt', '')).strip()
            visham = row.get('विषम-पद', row.get('visham-pada', '')).strip()
            sama = row.get('सम-पद', row.get('sama-pada', '')).strip()
            aksha = row.get('अक्षरसङ्ख्या', row.get('akshara', '')).strip()
            source = row.get('source', '')

            # Create a single mapped row using the target header: वृत्त,पद,लक्षण,लक्षण (raw),अक्षरसङ्ख्या,मात्रा,यति
            laksh = f"{visham} | {sama}" if visham or sama else visham or sama
            laksh_raw = laksh
            out_rows.append([vrtt, '', laksh, laksh_raw, aksha, '', source])

    # Backup existing target and write
    if target.exists():
        target.replace(backup)
    with target.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for r in out_rows:
            writer.writerow(r)

    print(f"Wrote merged ardhasama to {target} (backup at {backup if backup.exists() else 'none'})")


def merge_vishama():
    orig = ROOT / 'chanda_vishama.csv'
    imported = ROOT / 'chanda_vishama_imported.csv'
    target = ROOT / 'chanda_vishama.csv'
    backup = target.with_suffix(target.suffix + '.bak')

    out_rows = []
    with orig.open('r', encoding='utf-8') as f:
        reader = csv.reader(f)
        for r in reader:
            out_rows.append(r)

    with imported.open('r', encoding='utf-8') as f:
        dreader = csv.DictReader(f)
        for row in dreader:
            vrtt = row.get('वृत्त', row.get('vrtt', '')).strip()
            aksha = row.get('अक्षरसङ्ख्या', row.get('akshara', '')).strip()
            source = row.get('source', '')

            # Expect pad columns like 'पद-1','पद-2',... create one row per pad
            pad_keys = [k for k in row.keys() if k.startswith('पद') or k.startswith('pad')]
            # sort pad_keys to ensure order
            pad_keys = sorted(pad_keys, key=lambda x: int(''.join([c for c in x if c.isdigit()]) or 0))
            if not pad_keys:
                # fallback to trying 'पद-1'..'पद-4'
                pad_keys = [f'पद-{i}' for i in range(1, 5)]

            for idx, pk in enumerate(pad_keys, start=1):
                pad_pattern = (row.get(pk) or '').strip()
                if not pad_pattern:
                    continue
                # target row schema: वृत्त,पद,लक्षण,लक्षण (raw),अक्षरसङ्ख्या,मात्रा,यति
                laksh = f'पद{idx}'
                laksh_raw = pad_pattern
                out_rows.append([vrtt, str(idx), laksh, laksh_raw, aksha, '', source])

    # Backup and write
    if target.exists():
        target.replace(backup)
    with target.open('w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        for r in out_rows:
            writer.writerow(r)

    print(f"Wrote merged vishama to {target} (backup at {backup if backup.exists() else 'none'})")


def main():
    merge_ardhasama()
    merge_vishama()


if __name__ == '__main__':
    main()
