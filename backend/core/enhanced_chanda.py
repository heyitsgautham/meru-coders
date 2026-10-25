#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Enhanced Chanda Identifier

Implements all rules from Chandovallari (Dr. Sampadananda Mishra):
1. Pada-level exact pattern matching (Level 1.5)
2. 14 Upajāti varieties detection
3. Yati (caesura) validation
4. End-of-Quarter (Anta-guru) rule
5. Classical meter patterns with gaṇa definitions
6. Mātrā-based meter identification (Āryā family)
7. Samavṛtta/Ardhasamavṛtta/Viṣamavṛtta classification
8. Vedic tolerance (±1-2 syllables)

@author: Enhanced for SIH 2025
"""

###############################################################################

import csv
import functools
import os
import re
from collections import Counter, defaultdict

import sanskrit_text as skt
from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate

from .enhanced_chanda_matching import EnhancedMatchingMixin
from .enhanced_chanda_tables import EnhancedTables

# size of LRU cache
MAX_CACHE = 1024

###############################################################################


class EnhancedChanda(EnhancedTables, EnhancedMatchingMixin):
    """Enhanced Chanda Identifier with Chandovallari rules"""

    def __init__(self, data_path, symbols='यरतनभजसमलग'):
        """Initialize Enhanced Chanda identifier"""
        self.input_map = dict(zip(symbols, self.SYMBOLS, strict=False))
        self.output_map = dict(zip(self.SYMBOLS, symbols, strict=False))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {v: k for k, v in self.gana.items()}

        self.data_path = data_path

        # Definitions
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.MATRA = defaultdict(list)
        self.SPLITS = defaultdict(list)

        # Read Data
        self.read_data()

        # Build pada pattern index for fast lookup
        self._build_pada_pattern_index()

    ###########################################################################
    # Core L-G Marking
    ###########################################################################

    @functools.lru_cache(maxsize=MAX_CACHE)  # noqa: B019 - one long-lived engine per process
    def mark_lg(self, text):
        """Mark Laghu-Guru for text (matching original implementation)"""
        skip_syllables = [skt.AVAGRAHA]
        lg_marks = []
        syllables = skt.get_syllables(text)
        flat_syllables = [s for ln in syllables for w in ln for s in w]

        if not flat_syllables:
            return flat_syllables, lg_marks

        for idx, syllable in enumerate(flat_syllables[:-1]):
            if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
                lg_marks.append('')
                continue
            # A syllable is laghu if it's naturally short AND
            # the next syllable doesn't start with conjunct (no halanta)
            laghu = skt.is_laghu(syllable) and (skt.HALANTA not in flat_syllables[idx + 1])
            lg_marks.append(self.L if laghu else self.G)

        # Handle last syllable
        syllable = flat_syllables[-1]
        if syllable[-1] == skt.HALANTA or syllable in skip_syllables:
            lg_marks.append('')
        else:
            # End-of-Quarter rule: mark as actual weight
            lg_marks.append(self.L if skt.is_laghu(syllable) else self.G)

        return syllables, lg_marks

    ###########################################################################
    # Gaṇa Transformations
    ###########################################################################

    def lg_to_gana(self, lg_str):
        """Transform Laghu-Guru string into Gana string"""
        gana = []
        for i in range(0, len(lg_str), 3):
            group = lg_str[i : i + 3]
            gana.append(self.gana_inv.get(group, group))
        return ''.join(gana)

    def gana_to_lg(self, gana_str: str) -> str:
        """Transform Gana string into Laghu-Guru string"""
        return gana_str.translate(str.maketrans(self.gana))

    def count_matra(self, gana_str: str) -> int:
        """Count matra from a Gana or Laghu-Guru string"""
        lg_str = self.gana_to_lg(gana_str)
        return lg_str.count(self.L) + lg_str.count(self.G) * 2

    ###########################################################################
    # Pada Pattern Index (for fast pada-level matching)
    ###########################################################################

    def _build_pada_pattern_index(self):
        """Build index of pada patterns from CHANDA database"""
        self.PADA_INDEX = {}  # pattern -> [(meter_name, confidence)]

        # Add classical patterns with high confidence
        for pattern, (dev_name, _iast_name, _gana) in self.CLASSICAL_PADA_PATTERNS.items():
            self.PADA_INDEX[pattern] = [(dev_name, 9.8, 'classical_definition')]

        # Index pada patterns from loaded database
        for lg_pattern, meter_names in self.CHANDA.items():
            # Patterns with 11, 12, 13, 14, 15 syllables are pada-level
            if 11 <= len(lg_pattern) <= 21:
                for meter_name in meter_names:
                    name = meter_name[0] if isinstance(meter_name, tuple) else meter_name
                    if lg_pattern not in self.PADA_INDEX:
                        self.PADA_INDEX[lg_pattern] = []
                    self.PADA_INDEX[lg_pattern].append((name, 9.5, 'database'))

    ###########################################################################
    # Utility Methods
    ###########################################################################

    def split_into_padas(self, lg_pattern, num_padas=4):
        """Split L-G pattern into equal padas"""
        length = len(lg_pattern)
        if length % num_padas != 0:
            return None

        pada_length = length // num_padas
        padas = []
        for i in range(num_padas):
            start = i * pada_length
            end = start + pada_length
            padas.append(lg_pattern[start:end])

        return padas

    def classify_verse_type(self, lg_pattern):
        """
        Classify verse as Samavṛtta, Ardhasamavṛtta, or Viṣamavṛtta
        (From Chandovallari Section 4)
        """
        padas = self.split_into_padas(lg_pattern, 4)
        if not padas:
            return 'unknown'

        if all(pada == padas[0] for pada in padas):
            return 'samavṛtta'  # All 4 quarters identical
        elif padas[0] == padas[2] and padas[1] == padas[3]:
            return 'ardhasamavṛtta'  # 1st=3rd, 2nd=4th
        else:
            return 'viṣamavṛtta'  # All different

    def try_anta_guru_variants(self, lg_pattern):
        """
        Try matching with Anta-guru rule (End-of-Quarter rule)

        From Chandovallari: At end of quarter, short can be long and vice versa
        """
        variants = [lg_pattern]

        # Try flipping last character
        if lg_pattern[-1] == self.L:
            variants.append(lg_pattern[:-1] + self.G)
        else:
            variants.append(lg_pattern[:-1] + self.L)

        # For 4-pada verses, also try flipping end of each pada
        padas = self.split_into_padas(lg_pattern, 4)
        if padas:
            pada_length = len(padas[0])
            for i in range(4):
                pos = (i + 1) * pada_length - 1
                if pos < len(lg_pattern):
                    if lg_pattern[pos] == self.L:
                        variant = lg_pattern[:pos] + self.G + lg_pattern[pos + 1 :]
                    else:
                        variant = lg_pattern[:pos] + self.L + lg_pattern[pos + 1 :]
                    if variant not in variants:
                        variants.append(variant)

        return variants

    ###########################################################################
    # Data Loading
    ###########################################################################

    def read_jaati(self, file):
        """Read Jaati list from CSV"""
        jaati = defaultdict(list)
        with open(file, 'r', encoding='utf-8') as f:
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

        with open(chanda_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue

                if len(row) < 4:
                    continue

                chanda_names = tuple([c.strip() for c in row[0].split(',')])
                pada = tuple([c.strip() for c in row[1].split(',')]) if row[1] else ('',)
                gana_pattern = row[2].strip() if len(row) > 2 else ''
                lg_pattern = row[3].strip() if len(row) > 3 else ''

                if not lg_pattern and gana_pattern:
                    lg_pattern = self.gana_to_lg(gana_pattern.translate(self.ttable_in))

                if not lg_pattern:
                    continue

                lg_pattern = lg_pattern.upper().replace('U', self.L).replace('-', self.G)

                if pada == ('',):
                    for name in chanda_names:
                        chanda[lg_pattern].append((name, pada))
                else:
                    chanda_pada[chanda_names][pada] = lg_pattern

        # Process multi-pada meters
        for _chanda_names, _pada_lakshana in chanda_pada.items():
            multi_pada = []
            multi_lakshana = []
            for _pada, _lakshana in _pada_lakshana.items():
                multi_pada.append(_pada)
                multi_lakshana.append(_lakshana)

            if multi_lakshana:
                combined_lg = ''.join(multi_lakshana)
                for name in _chanda_names:
                    multi_chanda[combined_lg].append((name, tuple(multi_pada)))

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
        definition_files = ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_vedic.csv']
        for chanda_file in definition_files:
            file_path = os.path.join(self.data_path, chanda_file)
            if os.path.exists(file_path):
                self.read_chanda_definitions(file_path)

    ###########################################################################
    # Text Processing
    ###########################################################################

    def process_text(self, text):
        """Process text and convert to Devanagari"""
        scheme = detect(text)
        if scheme != sanscript.DEVANAGARI:
            devanagari_text = transliterate(text, scheme, sanscript.DEVANAGARI)
        else:
            devanagari_text = text

        lines = []
        for line in skt.split_lines(devanagari_text):
            clean_line = skt.clean(line).strip()
            if clean_line:
                lines.append(clean_line)

        return lines, scheme

    ###########################################################################
    # Main Identification Methods
    ###########################################################################

    def find_direct_match(self, line, multi=False):
        """Find direct match for a line"""
        chanda_dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA

        syllables, lg_marks = self.mark_lg(skt.clean(line))
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        lg_str = ''.join(lg_marks)

        if not lg_str:
            return None

        found = lg_str in chanda_dictionary

        # Try Anta-guru rule: flip last syllable
        if not found and lg_str[-1] == self.L:
            lg_str_guru = lg_str[:-1] + self.G
            found = lg_str_guru in chanda_dictionary
            if found:
                lg_str = lg_str_guru

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

        match = {
            'found': found,
            'syllables': flat_syllables,
            'lg': lg_marks,
            'gana': gana,
            'chanda': chanda,
            'jaati': jaati,
            'length': length,
            'matra': matra,
        }
        return match

    def identify_line(self, line, fuzzy=False, k=10):
        """Identify Chanda from a single line"""
        lines, scheme = self.process_text(line)
        output_scheme = scheme if scheme != sanscript.DEVANAGARI else None

        if len(lines) > 1:
            # Concatenate multi-line input
            line = ' '.join(lines)
        elif len(lines) == 1:
            line = lines[0]
        else:
            return {}

        answer = {}

        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            return answer

        found = direct_match['found'] or multi_match['found']
        lg_str = ''.join(direct_match['lg'])

        # Regex matches
        regex_matches = [k for k in self.CHANDA if re.match(f'^{k}$', lg_str)]
        if regex_matches:
            found = True
        is_regex_match = bool(regex_matches)

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []

        if found:
            if direct_match['found']:
                chanda.extend(direct_match['chanda'])
                jaati = direct_match['jaati']
                gana = direct_match['gana']
                length = direct_match['length']
                matra = direct_match['matra']
            if multi_match['found']:
                chanda.extend(multi_match['chanda'])
                if not jaati:
                    jaati = multi_match['jaati']
                length = multi_match.get('length', length)
                matra = multi_match.get('matra', matra)

            if is_regex_match:
                chanda += [c for m in regex_matches for c in self.CHANDA.get(m, []) if c not in chanda]

        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, []))

        # ENHANCED: Multi-level matching with confidence scores
        multi_level_matches = self.match_with_confidence(lg_str, fuzzy=fuzzy, max_fuzzy=k)

        # Build confidence map
        confidence_map = {}

        # Add existing exact matches
        for c in chanda:
            meter_name = c[0] if isinstance(c, tuple) else c
            confidence_map[meter_name] = (10.0, 'exact_direct')

        # Add multi-level matches
        for match_item, confidence, match_type in multi_level_matches:
            if isinstance(match_item, tuple):
                meter_name = match_item[0]
                meter_tuple = match_item
            else:
                meter_name = match_item
                meter_tuple = (match_item, ('',))

            # Don't let Vedic family names override specific meters
            if meter_name in self.VEDIC_FAMILY_NAMES:
                if any(m not in self.VEDIC_FAMILY_NAMES for m in confidence_map.keys()):
                    # We have specific meters, skip Vedic family
                    confidence = min(confidence, 3.0)

            if meter_name in confidence_map:
                existing_conf, existing_type = confidence_map[meter_name]
                if confidence > existing_conf:
                    confidence_map[meter_name] = (confidence, match_type)
            else:
                confidence_map[meter_name] = (confidence, match_type)
                if meter_tuple not in chanda:
                    chanda.append(meter_tuple)

        # Sort chanda by confidence
        chanda_with_confidence = [
            (name, confidence_map.get(name[0] if isinstance(name, tuple) else name, (0, ''))[0]) for name in chanda
        ]
        chanda_with_confidence.sort(key=lambda x: x[1], reverse=True)
        chanda = [item[0] for item in chanda_with_confidence]

        if chanda:
            found = True

        # Classify verse type
        verse_type = self.classify_verse_type(lg_str)

        # Display properties
        display_line = line
        display_syllables = direct_match['syllables']
        display_lg = full_lg
        display_gana = ' / '.join(gana).translate(self.ttable_out) if gana else full_gana
        display_length = ' / '.join(length) if length else str(full_length)
        display_matra = ' / '.join(matra) if matra else str(full_matra)
        display_chanda = ' / '.join((c[0] if isinstance(c, tuple) else str(c)) for c in chanda[:5]) if chanda else ''
        display_jaati = ' / '.join(jaati if jaati else full_jaati)

        answer['found'] = found
        answer['syllables'] = direct_match['syllables']
        answer['lg'] = ''.join(full_lg)
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati if jaati else full_jaati
        answer['confidence_scores'] = confidence_map
        answer['verse_type'] = verse_type

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
        answer['display_gana'] = display_gana
        answer['display_length'] = display_length
        answer['display_matra'] = display_matra
        answer['display_chanda'] = display_chanda
        answer['display_jaati'] = display_jaati

        answer['fuzzy'] = []

        # Add fuzzy results if not found
        if not found and fuzzy:
            fuzzy_results = self._fuzzy_match(lg_str, k)
            for name, conf, match_type in fuzzy_results:
                answer['fuzzy'].append({'name': name, 'confidence': conf, 'match_type': match_type})

        # Build results list for API compatibility
        answer['results'] = []
        for c in chanda[:k]:
            meter_name = c[0] if isinstance(c, tuple) else c
            conf, match_type = confidence_map.get(meter_name, (0, 'unknown'))
            answer['results'].append({'name': meter_name, 'confidence': conf, 'match_type': match_type})

        return answer

    def identify_from_text(self, text, verse=False, fuzzy=False, save_path=None, scheme=None):
        """Identify meters from text"""
        line_results = []
        verse_results = []

        lines, _scheme = self.process_text(text)
        if not scheme:
            scheme = _scheme

        for line in lines:
            if not line:
                continue
            original_line = transliterate(line, sanscript.DEVANAGARI, scheme)
            line_results.append({'line': line, 'result': self.identify_line(original_line, fuzzy=fuzzy)})

        if verse:
            verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}

            line_count = 0
            ongoing_score = Counter()

            for _line_idx, line_result in enumerate(line_results):
                line_count += 1
                result = line_result['result']

                if result.get('chanda'):
                    for c in result['chanda'][:3]:
                        name = c[0] if isinstance(c, tuple) else c
                        ongoing_score[name] += 1

                verse_result['lines'].append(line_result)

                if line_count == 4:
                    if ongoing_score:
                        best_chanda = ongoing_score.most_common(1)[0]
                        verse_result['chanda'] = best_chanda
                        verse_result['scores'] = ongoing_score.most_common()
                    verse_results.append(verse_result)

                    verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}
                    line_count = 0
                    ongoing_score = Counter()

            # Handle remaining lines
            if verse_result['lines']:
                if ongoing_score:
                    best_chanda = ongoing_score.most_common(1)[0]
                    verse_result['chanda'] = best_chanda
                    verse_result['scores'] = ongoing_score.most_common()
                verse_results.append(verse_result)

        results = {'line': line_results, 'verse': verse_results}

        return {
            'result': results,
            'results': line_results,  # For API compatibility
        }

    ###########################################################################
    # Formatters
    ###########################################################################

    @staticmethod
    def format_chanda_pada(chanda: str, pada: tuple) -> str:
        if not chanda:
            return ''
        if isinstance(pada, tuple) and len(pada) == 1 and pada[0] == '':
            return chanda
        elif isinstance(pada, tuple) and len(pada) > 1:
            return f"{chanda} ({', '.join(str(p) for p in pada)})"
        elif pada and str(pada) != '':
            return f"{chanda} ({pada})"
        return chanda


###############################################################################
