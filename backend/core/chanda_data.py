"""Loading the meter definition CSVs and example verses from the data directory.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""

import csv
import json
import os
from collections import defaultdict

import sanskrit_text as skt
from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate


class MeterDataMixin:
    ###########################################################################

    def read_jaati(self, file):
        """
        Read Jaati list from CSV

        @format:
            - First column contains number of letters
            - Second column contains name(s) of Jaati
        """
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

    def read_matra(self, file):
        """
        Read Mātrā-based meters from CSV

        @format:
            - First column contains meter name(s)
            - Second column contains mātrā sequence (e.g., '12181215' = 12-18-12-15)
            - Third column (optional) contains synonyms
        """
        matra_meters = defaultdict(list)
        with open(file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row[0].strip():
                    continue

                names = [row[0].strip()]
                if len(row) > 2 and row[2].strip():
                    # Add synonyms
                    synonyms = [s.strip() for s in row[2].split(',')]
                    names.extend(synonyms)

                matra_sequence = row[1].strip()

                # Parse mātrā sequence: '12181215' -> [12, 18, 12, 15]
                pada_matras = []
                i = 0
                while i < len(matra_sequence):
                    if i + 1 < len(matra_sequence):
                        # Try two-digit number
                        two_digit = matra_sequence[i : i + 2]
                        if two_digit.isdigit() and 10 <= int(two_digit) <= 30:
                            pada_matras.append(int(two_digit))
                            i += 2
                            continue
                    # Single digit
                    if matra_sequence[i].isdigit():
                        pada_matras.append(int(matra_sequence[i]))
                        i += 1
                    else:
                        i += 1

                # Store by mātrā sequence
                for name in names:
                    matra_meters[matra_sequence].append(name)
                    # Also store by total mātrā count for quick lookup
                    total_matras = sum(pada_matras)
                    if len(pada_matras) >= 2:
                        # Store with pattern signature
                        pattern_key = f"matra_{total_matras}_{len(pada_matras)}"
                        matra_meters[pattern_key].append(name)

        self.MATRA.update(matra_meters)
        return matra_meters

    def read_chanda_definitions(self, chanda_file):
        """
        Read definitions of Chanda from CSV

        @params:
            - file: path of the CSV file containing Chanda definitions

        @format:
            Chanda definition file should have at least 3 columns
                - First column should contain name(s) of Chanda/VRtta
                - Second column should contain Pada
                - Third column should contain the Gana string
            Remaing columns will be ignored.
        """
        chanda = defaultdict(list)
        multi_chanda = defaultdict(list)
        splits = defaultdict(list)

        chanda_pada = defaultdict(dict)

        # Check if this is vedic CSV to extract pada patterns
        is_vedic_file = 'vedic' in chanda_file.lower()

        with open(chanda_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = True
            for row in reader:
                if header:
                    header = False
                    continue
                if not row[0].strip():
                    continue

                # `meters` is a tuple since we need it to be hashable
                # for use as a key in the dictionary `chanda_pada`
                names = tuple(c.strip() for c in row[0].split(','))
                pada = row[1].strip()
                # meters = ((chanda, pada), ...)
                meters = tuple((c, (pada,)) for c in names)
                gana_notation = ''.join(row[2].split()) if len(row) > 2 else ''
                lakshana = gana_notation.translate(self.ttable_in)
                lakshana = self.gana_to_lg(lakshana)
                lakshana = lakshana.replace('-', f"[{self.L}{self.G}]")

                # Extract raw L-G pattern and syllable/matra counts from CSV
                raw_lg_pattern = row[3].strip() if len(row) > 3 else ''
                syllable_count = int(row[4].strip()) if len(row) > 4 and row[4].strip().isdigit() else len(lakshana)
                matra_count = int(row[5].strip()) if len(row) > 5 and row[5].strip().isdigit() else 0
                yati = row[6].strip() if len(row) > 6 else ''

                # Store comprehensive meter info for pattern validation display
                meter_type = (
                    'vedic'
                    if is_vedic_file
                    else 'sama'
                    if 'sama' in chanda_file.lower()
                    else 'vishama'
                    if 'vishama' in chanda_file.lower()
                    else 'ardhasama'
                )
                for name in names:
                    if name not in self.METER_INFO:
                        self.METER_INFO[name] = {
                            'pattern': raw_lg_pattern or lakshana,
                            'pattern_internal': lakshana,
                            'syllables': syllable_count,
                            'matras': matra_count,
                            'gana': gana_notation,
                            'type': meter_type,
                            'yati': yati,
                            'padas': {},
                        }
                    # Store pada-specific pattern if pada number specified
                    if pada:
                        self.METER_INFO[name]['padas'][pada] = {
                            'pattern': raw_lg_pattern or lakshana,
                            'syllables': syllable_count,
                            'matras': matra_count,
                            'gana': gana_notation,
                        }

                # Store Vedic pada patterns for enhanced matching
                if is_vedic_file and lakshana:
                    meter_name = names[0]
                    if meter_name not in self.VEDIC_PADA_PATTERNS:
                        self.VEDIC_PADA_PATTERNS[meter_name] = lakshana

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

                    # FIX 3: For ardhasama meters, also store the REVERSE order
                    # This handles cases where input might have pada2 before pada1
                    # e.g., upacitrā has different patterns for odd/even padas
                    if 'ardhasama' in chanda_file.lower():
                        reversed_lakshana = multi_lakshana[::-1]
                        reversed_key = ''.join(reversed_lakshana)
                        if reversed_key != ''.join(multi_lakshana):
                            multi_chanda[reversed_key].extend(names)
                            splits[reversed_key].append(reversed_lakshana)

                    multi_pada = []
                    multi_lakshana = []

        # FIX 3: For ardhasama meters, also create 4-pada combined patterns
        # Many ardhasama have alternating patterns: pada1-pada2-pada1-pada2
        if 'ardhasama' in chanda_file.lower():
            for _chanda_names, _pada_lakshana in chanda_pada.items():
                if '1' in _pada_lakshana and '2' in _pada_lakshana:
                    p1 = _pada_lakshana['1']
                    p2 = _pada_lakshana['2']

                    # Create 4-pada patterns (common for full shloka)
                    # Pattern: 1-2-1-2 (standard ardhasama)
                    four_pada_1212 = p1 + p2 + p1 + p2
                    # Pattern: 1-2-2-1 (less common)
                    four_pada_1221 = p1 + p2 + p2 + p1

                    names_4pada = tuple((_name, ('1', '2', '3', '4')) for _name in _chanda_names)

                    # Only add if not already present
                    if four_pada_1212 not in multi_chanda:
                        multi_chanda[four_pada_1212].extend(names_4pada)
                    if four_pada_1221 not in multi_chanda:
                        multi_chanda[four_pada_1221].extend(names_4pada)

        for k, v in chanda.items():
            self.SINGLE_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)
        for k, v in multi_chanda.items():
            self.MULTI_CHANDA[k].extend(v)
            self.CHANDA[k].extend(v)

        self.SPLITS.update(splits)
        return chanda

    # ----------------------------------------------------------------------- #

    def read_data(self):
        self.read_jaati(os.path.join(self.data_path, 'chanda_jaati.csv'))
        self.read_matra(os.path.join(self.data_path, 'chanda_matra.csv'))
        definition_files = ['chanda_sama.csv', 'chanda_ardhasama.csv', 'chanda_vishama.csv', 'chanda_vedic.csv']
        for chanda_file in definition_files:
            self.read_chanda_definitions(os.path.join(self.data_path, chanda_file))

    # ----------------------------------------------------------------------- #

    def read_examples(self):
        example_file = os.path.join(self.data_path, "examples.json")
        with open(example_file, "r", encoding="utf-8") as f:
            examples = json.load(f)
        return examples

    ###########################################################################

    def process_text(self, text):
        scheme = detect(text)
        if scheme != sanscript.DEVANAGARI:
            devanagari_text = transliterate(text, scheme, sanscript.DEVANAGARI)
        else:
            devanagari_text = text

        # Always normalize Vedic characters (lightweight operation)
        # This handles special Unicode characters in Vedic texts
        devanagari_text = self.normalize_vedic_characters(devanagari_text)

        # Additional Vedic preprocessing for specific markers
        if self.detect_vedic_markers(devanagari_text):
            devanagari_text = self.preprocess_vedic_text(devanagari_text)

        lines = []
        for line in skt.split_lines(devanagari_text):
            clean_line = skt.clean(line).strip()
            if clean_line:
                lines.append(clean_line)
        return lines, scheme
