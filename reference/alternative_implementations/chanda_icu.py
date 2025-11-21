#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ICU-based Syllabization Implementation
Uses PyICU for grapheme-based syllable splitting (from sanskrit-coders/chandas)
"""

import os
import re
import csv
import functools
from collections import defaultdict, Counter

import icu
import regex
from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate

# size of LRU cache
MAX_CACHE = 1024


class ChandaICU:
    """Chanda Identifier using ICU-based syllabization"""
    
    Y = 'Y'
    R = 'R'
    T = 'T'
    N = 'N'
    B = 'B'
    J = 'J'
    S = 'S'
    M = 'M'
    L = 'L'
    G = 'G'
    SYMBOLS = f'{Y}{R}{T}{N}{B}{J}{S}{M}{L}{G}'
    GANA = {
        Y: f'{L}{G}{G}',
        R: f'{G}{L}{G}',
        T: f'{G}{G}{L}',
        N: f'{L}{L}{L}',
        B: f'{G}{L}{L}',
        J: f'{L}{G}{L}',
        S: f'{L}{L}{G}',
        M: f'{G}{G}{G}'
    }
    
    def __init__(self, data_path, symbols='यरतनभजसमलग'):
        self.input_map = dict(zip(symbols, self.SYMBOLS))
        self.output_map = dict(zip(self.SYMBOLS, symbols))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {v: k for k, v in self.gana.items()}
        
        self.data_path = data_path
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.SPLITS = defaultdict(list)
        
        self.read_data()
    
    # ICU-based syllabization (from repos/chandas)
    def get_graphemes(self, in_string):
        """Split a devanagari string into graphemes using ICU"""
        break_iterator = icu.BreakIterator.createCharacterInstance(icu.Locale())
        break_iterator.setText(in_string)
        i = 0
        graphemes = []
        for j in break_iterator:
            s = in_string[i:j]
            graphemes.append(s)
            i = j
        return graphemes
    
    def is_vyanjanaanta(self, in_string):
        """Check if string ends with virama"""
        return in_string.endswith('्') or in_string.endswith('य्ँ') or in_string.endswith('व्ँ') or in_string.endswith('ल्ँ')
    
    def has_vowel(self, in_string):
        """Check if string has a vowel"""
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]
        return bool(regex.findall("[%s%s]" % (dev_scheme.PATTERN_INDEPENDENT_VOWEL, dev_scheme.PATTERN_DEPENDENT_VOWEL), in_string, flags=regex.UNICODE) or regex.match(".*[%s](?=([^्]|$))" % (dev_scheme.PATTERN_VYANJANA), in_string, flags=regex.UNICODE))
    
    def begins_with_vowel(self, in_string):
        """Check if string begins with vowel"""
        return bool(regex.fullmatch(r"[ऄ-औॲ-ॷ].*", in_string, flags=regex.UNICODE))
    
    @functools.lru_cache(maxsize=MAX_CACHE)
    def get_syllables(self, in_string):
        """Split devanagari string into syllables using ICU logic"""
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]
        cleaned_phrase = in_string
        
        # Preprocess OM
        cleaned_phrase = regex.sub("[%s]" % dev_scheme.PATTERN_OM, "ओम्", cleaned_phrase)
        
        # Remove non-letter characters
        cleaned_phrase = regex.sub(r"([^%s%s%s%s%s%s])" % (
            dev_scheme.PATTERN_INDEPENDENT_VOWEL, 
            dev_scheme.PATTERN_VYANJANA, 
            dev_scheme.PATTERN_DEPENDENT_VOWEL, 
            dev_scheme.PATTERN_YOGAVAAHA, 
            dev_scheme.PATTERN_ACCENT, 
            dev_scheme.PATTERN_CONSONANT_MODIFIER
        ), "", cleaned_phrase, flags=regex.UNICODE)
        
        cleaned_phrase = cleaned_phrase.replace(" ", "")
        
        # Join vyanjana + independent vowel
        cleaned_phrase = regex.sub(
            r"(%s)([%s])" % (dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL, dev_scheme.PATTERN_INDEPENDENT_VOWEL), 
            lambda x: sanscript.SCHEMES[sanscript.DEVANAGARI].do_vyanjana_svara_join(x.group(1), x.group(2)), 
            cleaned_phrase
        )
        
        syllables = []
        while len(cleaned_phrase) > 0:
            match = regex.match(
                (r"(%s)*[%s%s]़?[%s]*[%s]*[%s]*(%sँ?)*" % (
                    dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL,
                    dev_scheme.PATTERN_INDEPENDENT_VOWEL, 
                    dev_scheme.PATTERN_VYANJANA, 
                    dev_scheme.PATTERN_DEPENDENT_VOWEL, 
                    dev_scheme.PATTERN_YOGAVAAHA, 
                    dev_scheme.PATTERN_ACCENT, 
                    dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL
                )), 
                cleaned_phrase
            )
            if match is None:
                break
            current_syllable = match.group(0)
            cleaned_phrase = cleaned_phrase.replace(match.group(0), "", 1)
            if len(current_syllable) > 0:
                syllables.append(current_syllable)
        
        return syllables
    
    def get_syllable_weight(self, syllable):
        """Get weight (L/G) of a syllable"""
        dev_scheme = sanscript.SCHEMES[sanscript.DEVANAGARI]
        
        # Check for guru vowels
        if regex.findall(r"[%s%s%s]" % (
            dev_scheme.PATTERN_GURU_INDEPENDENT_VOWEL, 
            dev_scheme.PATTERN_GURU_DEPENDENT_VOWEL, 
            dev_scheme.PATTERN_GURU_YOGAVAAHA
        ), syllable):
            return self.G
        
        # Check for conjunct consonants (makes it guru)
        elif regex.findall(r"[%s%s]़?[%s]*[%s]*[%s]*(%s)+" % (
            dev_scheme.PATTERN_INDEPENDENT_VOWEL, 
            dev_scheme.PATTERN_VYANJANA, 
            dev_scheme.PATTERN_DEPENDENT_VOWEL, 
            dev_scheme.PATTERN_YOGAVAAHA, 
            dev_scheme.PATTERN_ACCENT, 
            dev_scheme.PATTERN_VYANJANA_WITHOUT_VOWEL
        ), syllable):
            return self.G
        else:
            return self.L
    
    @functools.lru_cache(maxsize=MAX_CACHE)
    def mark_lg(self, text):
        """Mark Laghu-Guru using ICU syllabization"""
        syllables = self.get_syllables(text)
        lg_marks = [self.get_syllable_weight(syl) for syl in syllables]
        return [syllables], lg_marks
    
    def lg_to_gana(self, lg_str):
        """Transform Laghu-Guru string into Gana string"""
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i:i+3]
            gana.append(self.gana_inv.get(group, group))
        return ''.join(gana)
    
    def gana_to_lg(self, gana_str: str) -> str:
        """Transform Gana string into Laghu-Guru string"""
        return gana_str.translate(str.maketrans(self.gana))
    
    def count_matra(self, gana_str: str) -> int:
        """Count matra from a Gana or Laghu-Guru string"""
        lg_str = self.gana_to_lg(gana_str)
        return lg_str.count(self.L) + lg_str.count(self.G) * 2
    
    def read_jaati(self, file):
        """Read Jaati list from CSV"""
        jaati = defaultdict(list)
        with open(file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                letter_count = int(row[0].strip())
                names = [c.strip() for c in row[1].split(',')]
                jaati[letter_count] = tuple(names)
        self.JAATI.update(jaati)
        return jaati
    
    def read_chanda_definitions(self, chanda_file):
        """Read definitions of Chanda from CSV"""
        chanda = defaultdict(list)
        multi_chanda = defaultdict(list)
        splits = defaultdict(list)
        chanda_pada = defaultdict(dict)
        
        with open(chanda_file, 'r') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row[0].strip():
                    continue
                
                names = tuple(c.strip() for c in row[0].split(','))
                pada = row[1].strip()
                meters = tuple((c, (pada,)) for c in names)
                lakshana = ''.join(row[2].split())
                lakshana = lakshana.translate(self.ttable_in)
                lakshana = self.gana_to_lg(lakshana)
                lakshana = lakshana.replace('-', f"[{self.L}{self.G}]")
                
                if pada:
                    chanda_pada[names][pada] = lakshana
                else:
                    chanda_pada[names]['1'] = lakshana
                    chanda_pada[names]['2'] = lakshana
                
                if lakshana:
                    chanda[lakshana].extend(meters)
        
        for _chanda_names, _pada_lakshana in chanda_pada.items():
            multi_pada = []
            multi_lakshana = []
            for _pada, _lakshana in _pada_lakshana.items():
                multi_pada.append(_pada)
                multi_lakshana.append(_lakshana)
                
                if len(multi_pada) == 2:
                    names = tuple((_name, tuple(multi_pada)) for _name in _chanda_names)
                    multi_chanda[''.join(multi_lakshana)].extend(names)
                    splits[''.join(multi_lakshana)].append(multi_lakshana)
                    multi_pada = []
                    multi_lakshana = []
        
        for k, v in chanda.items():
            self.SINGLE_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        for k, v in multi_chanda.items():
            self.MULTI_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        
        self.SPLITS.update(splits)
        return chanda
    
    def read_data(self):
        """Read all data files"""
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        definition_files = [
            'chanda_sama.csv', 'chanda_ardhasama.csv', 
            'chanda_vishama.csv', 'chanda_vedic.csv'
        ]
        for chanda_file in definition_files:
            self.read_chanda_definitions(os.path.join(self.data_path, chanda_file))
    
    def find_direct_match(self, line, multi=False):
        """Find direct match for a line"""
        chanda_dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA
        
        syllables, lg_marks = self.mark_lg(line)
        flat_syllables = syllables[0] if syllables else []
        lg_str = ''.join(lg_marks)
        
        if not lg_str:
            return None
        
        found = lg_str in chanda_dictionary
        
        # Try with last syllable as guru (anta-guru)
        if not found and lg_str[-1] == self.L:
            lg_str = lg_str[:-1] + self.G
            found = lg_str in chanda_dictionary
            if not found:
                lg_str = lg_str[:-1] + self.L
        
        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []
        
        if not multi:
            if found:
                chanda = self.SINGLE_CHANDA.get(lg_str, [])
            jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, []))
            gana = [self.lg_to_gana(lg_str)]
            length = [str(len(lg_str))]
            matra = [str(self.count_matra(lg_str))]
        else:
            if found:
                chanda = self.MULTI_CHANDA.get(lg_str, [])
                splits_data = self.SPLITS.get(lg_str, [])
                if splits_data:
                    jaati = [
                        "(" + ', '.join(
                            ' / '.join(self.JAATI.get(len(split), self.JAATI.get(-1, [])))
                            for split in splits
                        ) + ")"
                        for splits in splits_data
                    ]
                    gana = [
                        f"({', '.join(self.lg_to_gana(s) for s in splits)})"
                        for splits in splits_data
                    ]
                    length = [
                        f"({' + '.join(str(len(s)) for s in splits)})"
                        for splits in splits_data
                    ]
                    matra = [
                        f"({' + '.join(str(self.count_matra(s)) for s in splits)})"
                        for splits in splits_data
                    ]
        
        return {
            'found': found,
            'syllables': flat_syllables,
            'lg': lg_marks,
            'gana': gana,
            'chanda': chanda,
            'jaati': jaati,
            'length': length,
            'matra': matra
        }
    
    def identify_line(self, line):
        """Identify Chanda from a single line"""
        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)
        
        if direct_match is None:
            return {}
        
        found = direct_match['found'] or multi_match['found']
        lg_str = ''.join(direct_match['lg'])
        
        # Check regex matches
        regex_matches = [k for k in self.CHANDA if re.match(f'^{k}$', lg_str)]
        if regex_matches:
            found = True
        
        chanda = []
        if found:
            if direct_match['found']:
                chanda += direct_match['chanda']
            if multi_match['found']:
                chanda += multi_match['chanda']
            if regex_matches:
                chanda += [c for m in regex_matches for c in self.CHANDA.get(m) if c not in chanda]
        
        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        
        return {
            'found': found,
            'syllables': direct_match['syllables'],
            'lg': full_lg,
            'gana': full_gana,
            'length': full_length,
            'chanda': chanda,
            'lg_str': lg_str
        }
    
    def identify_from_text(self, text, verse=False):
        """Identify meters from text"""
        line_results = []
        verse_results = []
        
        # Simple line splitting
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for line in lines:
            result = self.identify_line(line)
            line_results.append({'line': line, 'result': result})
        
        if verse:
            # Aggregate every 4 lines as a verse
            ongoing_score = Counter()
            for idx, line_result in enumerate(line_results):
                _result = line_result['result']
                if _result.get('found'):
                    for _c in _result['chanda']:
                        ongoing_score[_c] += 1
                
                if (idx + 1) % 4 == 0 or idx == len(line_results) - 1:
                    verse_scores = ongoing_score.most_common()
                    if verse_scores:
                        best_score = verse_scores[0][1]
                        best_matches = ([_c for _c, _score in verse_scores if _score == best_score], best_score)
                    else:
                        best_matches = ([], 0)
                    verse_results.append({'chanda': best_matches, 'scores': verse_scores})
                    ongoing_score = Counter()
        
        return {'line': line_results, 'verse': verse_results}
