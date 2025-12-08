#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Analyze Anushtubh pattern for BG 1.1"""

print('=' * 60)
print('Anushtubh analysis for Bhagavad Gita 1.1')
print('=' * 60)

print()
print('धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः')
print()

print('Pathya Anushtubh pattern:')
print('  Odd padas (1, 3):  x x x x L G G x')
print('  Even padas (2, 4): x x x x L G L x')
print()

print('Pada 1 (धर्मक्षेत्रे): ध-र्म-क्षे-त्रे = G G G G (all guru)')
print('Pada 2 (कुरुक्षेत्रे): कु-रु-क्षे-त्रे = L G G G')
print()
print('Pada 3 (समवेता): स-म-वे-ता = L L G G')
print('Pada 4 (युयुत्सवः): यु-यु-त्स-वः = ? ? L G')
print()

print('Question: What should the pattern be for युयुत्सवः?')
print()
print('Traditional prosody rule: संयोगपूर्वो गुरुः')
print('A short vowel before a consonant cluster is Guru by position.')
print()
print('Analysis of युयुत्सवः:')
print('  - यु (first): short vowel उ, followed by single consonant य → LAGHU')
print('  - यु (second): short vowel उ, followed by त्स (2 consonants) → GURU by position')
print('  - त्स: short vowel (inherent अ), followed by single consonant व → LAGHU')  
print('  - वः: has visarga ः → GURU')
print()
print('Expected pattern: L G L G')
print()
print('If the application is showing L G L G, it is CORRECT!')
print('The second यु is Guru by position (samyoga rule).')
