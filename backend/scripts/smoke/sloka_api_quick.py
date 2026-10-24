#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Quick test for Sloka Search API"""


import requests

# Test the sloka search endpoint with the first Rigveda verse
response = requests.post('http://localhost:5000/api/sloka/search', json={
    'text': 'अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं',
    'threshold': 0.5,
    'limit': 5
})

print('Status:', response.status_code)
data = response.json()
print('Success:', data.get('success'))
print('Match Count:', data.get('match_count'))
print('Total Indexed:', data.get('total_slokas_indexed'))
print('Has Exact Match:', data.get('has_exact_match'))
print('Best Similarity:', data.get('best_similarity'))

if data.get('matches'):
    print('\n--- Matches ---')
    for i, match in enumerate(data['matches'][:3]):
        print(f'\nMatch {i+1}:')
        print(f'  Similarity: {match["similarity"]}')
        print(f'  Exact: {match["is_exact_match"]}')
        print(f'  Chandas: {match["chandas"]}')
        print(f'  Dataset: {match["dataset_name"]}')
        print(f'  Text: {match["original_text"][:100]}...')
else:
    print('\nNo matches found.')
    print('Query:', data.get('query'))
    print('Query Normalized:', data.get('query_normalized'))

# Test with a modified (erroneous) verse
print('\n\n=== Testing with a slightly wrong verse ===')
response2 = requests.post('http://localhost:5000/api/sloka/validate', json={
    'text': 'अग्निमीले पुरोहितम यज्ञस्य देवमृत्विजम'  # Wrong spelling: मीले instead of मीळे
})

data2 = response2.json()
print('Status:', response2.status_code)
print('Success:', data2.get('success'))
print('Found:', data2.get('found'))
print('Valid:', data2.get('is_valid'))
print('Similarity:', data2.get('similarity_percentage'), '%')
print('Difference Count:', data2.get('difference_count'))
print('Message:', data2.get('message'))

if data2.get('differences'):
    print('\nDifferences:')
    for diff in data2['differences'][:5]:
        print(f'  - {diff["description"]}')
