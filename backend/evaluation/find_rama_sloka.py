"""Find the exact 'माता रामो' sloka in database"""
import csv

print('Searching for माता रामो...')
with open('source/chandovallari.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        sloka = row.get('Shloka ', '')
        if 'माता रामो' in sloka or 'रामचन्द्र' in sloka:
            print('='*60)
            print(f'METER: {row.get("chanda", "")}')
            print('SLOKA:')
            print(sloka)
            print('='*60)
            print()
