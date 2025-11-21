#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FINAL BENCHMARK: Focus on the critical visarga boundary issue
"""

import chanda
import chanda_option1_boundary_fix as opt1
import chanda_option2_icu_enhanced as opt2

print("="*80)
print("FINAL BENCHMARK: Visarga Boundary Syllabization")
print("="*80)
print()

# Test case that exposes the bug
test_text = "धियो यो नः प्रचोदयात्"
print(f"Test: {test_text}")
print()
print("Expected syllables: धि, यो, यो, नः, प्र, चो, द, यात् (8 syllables)")
print("Key: 'नः' and 'प्र' should be SEPARATE syllables")
print()

# Test all three
c_orig = chanda.Chanda('data/')
r_orig = c_orig.identify_line(test_text)

c_opt1 = opt1.Chanda('data/')
r_opt1 = c_opt1.identify_line(test_text)

c_opt2 = opt2.Chanda('data/', syllabization_method='icu')
r_opt2 = c_opt2.identify_line(test_text)

print("-"*80)
print("ORIGINAL (sanskrit_text):")
print(f"  Syllables: {r_orig['syllables']}")
print(f"  Count: {len(r_orig['syllables'])}")
correct_orig = r_orig['syllables'][3:5] == ['नः', 'प्र']
print(f"  नः/प्र separate? {'✓ YES' if correct_orig else '✗ NO - Merged as: ' + str(r_orig['syllables'][3:5])}")
print()

print("-"*80)
print("OPTION 1 (Boundary-Preserving):")
print(f"  Syllables: {r_opt1['syllables']}")
print(f"  Count: {len(r_opt1['syllables'])}")
correct_opt1 = r_opt1['syllables'][3:5] == ['नः', 'प्र']
print(f"  नः/प्र separate? {'✓ YES' if correct_opt1 else '✗ NO - Merged as: ' + str(r_opt1['syllables'][3:5])}")
print()

print("-"*80)
print("OPTION 2 (ICU Enhanced):")
print(f"  Syllables: {r_opt2['syllables']}")
print(f"  Count: {len(r_opt2['syllables'])}")
correct_opt2 = r_opt2['syllables'][3:5] == ['नः', 'प्र']
print(f"  नः/प्र separate? {'✓ YES' if correct_opt2 else '✗ NO - Merged as: ' + str(r_opt2['syllables'][3:5])}")
print()

print("="*80)
print("CONCLUSION:")
print("="*80)

if correct_opt2 and not correct_orig:
    print("✅ OPTION 2 (ICU Enhanced) FIXES THE BUG!")
    print("   Correctly separates visarga+consonant across word boundaries")
    print()
    print("RECOMMENDATION: Integrate Option 2 into chanda.py")
elif correct_opt1 and not correct_orig:
    print("✅ OPTION 1 (Boundary-Preserving) FIXES THE BUG!")
    print("   Correctly separates visarga+consonant across word boundaries")
    print()
    print("RECOMMENDATION: Integrate Option 1 into chanda.py")
else:
    print("⚠️  Need further investigation")

print("="*80)
