"""Search for user's sloka in database and provide test slokas"""

import csv
import os

# Search for 'माता रामो' or 'शालिन्युक्ता' in all CSVs
search_terms = ['माता रामो', 'शालिन्युक्ता', 'रामचन्द्र', 'शालिनी']
files = [
    'source/chandovallari.csv',
    'source/rigveda-with-meters.csv',
    'source/atharvaveda.csv',
    'source/chandas-as-vedanga.csv',
]

print('=== SEARCHING FOR YOUR SLOKA ===')
found_any = False
for f in files:
    if not os.path.exists(f):
        continue
    try:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            for term in search_terms:
                if term in content:
                    print(f'Found "{term}" in {f}!')
                    found_any = True
    except Exception as e:
        print(f'Error reading {f}: {e}')

if not found_any:
    print('Your sloka (माता रामो मत्पिता रामचन्द्रः) was NOT FOUND in our database!')
    print('This is why it shows as having "errors" - there is nothing to match against.')

print()
print('=' * 60)
print('=== VALID TEST SLOKAS FROM DATABASE (COPY-PASTE THESE) ===')
print('=' * 60)
print()

# Get actual slokas from the database
print('--- TEST 1: From Rigveda (Gayatri meter) ---')
with open('source/rigveda-with-meters.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    sloka = row.get('verse_text', '').strip()
    print(f'CORRECT: {sloka}')
    print(f'WITH ERROR (change ळ to ल): {sloka.replace("ळ", "ल")}')
    print()

print('--- TEST 2: From Chandovallari (Mandakranta meter) ---')
with open('source/chandovallari.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    row = next(reader)
    sloka = row.get('Shloka ', '').strip()
    # Get just first line
    first_line = sloka.split('\n')[0].strip()
    print(f'CORRECT: {first_line}')
    print(f'WITH ERROR (remove one char): {first_line[:20] + first_line[21:]}')
    print()

print('--- TEST 3: From Chandovallari (Drutavilambita meter) ---')
with open('source/chandovallari.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for i, row in enumerate(reader):
        if i == 2:  # Third row
            sloka = row.get('Shloka ', '').strip()
            first_line = sloka.split('\n')[0].strip()
            print(f'CORRECT: {first_line}')
            print(f'WITH ERROR (change ध to द): {first_line.replace("ध", "द")}')
            break
print()

print('=' * 60)
print('INSTRUCTIONS:')
print('1. Copy any "CORRECT" sloka above and paste into the checker')
print('2. It should show 100% match with green')
print('3. Then try the "WITH ERROR" version - it should highlight the error in red')
print('=' * 60)
