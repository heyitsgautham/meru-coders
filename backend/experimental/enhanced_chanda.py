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
from collections import defaultdict

import sanskrit_text as skt
from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate

from .enhanced_chanda_identify import EnhancedIdentifyMixin
from .enhanced_chanda_matching import EnhancedMatchingMixin
from .enhanced_chanda_tables import EnhancedTables

# size of LRU cache
MAX_CACHE = 1024

###############################################################################


class EnhancedChanda(EnhancedIdentifyMixin, EnhancedTables, EnhancedMatchingMixin):
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

    ###########################################################################
    # Formatters
    ###########################################################################


###############################################################################
