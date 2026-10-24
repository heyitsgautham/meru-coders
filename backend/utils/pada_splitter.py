#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pada Splitter - Split Sanskrit verses into padas based on chandas patterns

This module takes a Sanskrit verse (Devanagari or transliteration) and splits it 
into padas based on the identified chandas. It counts syllables by counting vowels
and follows standard meter patterns (e.g., Gayatri = 6-6-6-6, Anushtubh = 8-8-8-8).

Features:
- Preserves whole words when possible
- Only splits words when necessary to match exact syllable count
- Supports both Devanagari and transliterated input
- Handles common Vedic and Classical meters
- Loads Viṣamavṛtta (unequal) meters from CSV files

Usage:
    from pada_splitter import PadaSplitter
    splitter = PadaSplitter()
    padas = splitter.split_verse("धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः", meter="anushtubh")
"""

import csv
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from indic_transliteration import sanscript
from indic_transliteration.detect import detect
from indic_transliteration.sanscript import transliterate


@dataclass
class Pada:
    """Represents a single pada (quarter) of a verse"""
    text: str
    syllable_count: int
    position: int  # 1, 2, 3, or 4

    def __str__(self):
        return f"Pada {self.position}: {self.text} ({self.syllable_count} syllables)"


@dataclass
class SplitResult:
    """Result of splitting a verse into padas"""
    original_text: str
    meter: str
    meter_pattern: List[int]
    padas: List[Pada]
    total_syllables: int
    success: bool
    message: str

    def __str__(self):
        lines = [
            f"Meter: {self.meter}",
            f"Pattern: {'-'.join(map(str, self.meter_pattern))}",
            f"Total syllables: {self.total_syllables}",
            "---"
        ]
        for pada in self.padas:
            lines.append(str(pada))
        return '\n'.join(lines)


class PadaSplitter:
    """
    Split Sanskrit verses into padas based on chandas patterns.
    
    Meters supported:
    - Gayatri: 6-6-6-6 (24 syllables, 4 padas of 6)
      Note: Traditional Gayatri is 3 padas of 8, but 4×6 is also used
    - Anushtubh: 8-8-8-8 (32 syllables, 4 padas of 8)
    - Trishtubh: 11-11-11-11 (44 syllables, 4 padas of 11)
    - Jagati: 12-12-12-12 (48 syllables, 4 padas of 12)
    - Gayatri (Vedic): 8-8-8 (24 syllables, 3 padas of 8)
    - Ushnik: 7-7-7-7 (28 syllables, 4 padas of 7)
    - Brihati: 9-9-9-9 (36 syllables, 4 padas of 9)
    - Pankti: 8-8-8-8-8 (40 syllables, 5 padas of 8)
    """

    # Standard meter definitions: name -> list of syllable counts per pada
    METERS: Dict[str, List[int]] = {
        # Classical meters
        'gayatri': [6, 6, 6, 6],      # Classical Gayatri (4×6 = 24)
        'gayatri_vedic': [8, 8, 8],    # Vedic Gayatri (3×8 = 24)
        'anushtubh': [8, 8, 8, 8],     # Shloka meter (4×8 = 32)
        'trishtubh': [11, 11, 11, 11], # Trishtubh (4×11 = 44)
        'jagati': [12, 12, 12, 12],    # Jagati (4×12 = 48)

        # Additional Vedic meters
        'ushnik': [7, 7, 7, 7],        # Ushnik (4×7 = 28)
        'brihati': [9, 9, 9, 9],       # Brihati (4×9 = 36)
        'pankti': [8, 8, 8, 8, 8],     # Pankti (5×8 = 40)

        # Common classical meters with specific pada structures
        'indravajra': [11, 11, 11, 11],       # Same as Trishtubh
        'upendravajra': [11, 11, 11, 11],     # Same pattern
        'vasantatilaka': [14, 14, 14, 14],    # 4×14 = 56
        'mandakranta': [17, 17, 17, 17],      # 4×17 = 68
        'shardula_vikridita': [19, 19, 19, 19], # 4×19 = 76
        'sragdhara': [21, 21, 21, 21],        # 4×21 = 84

        # Half-verses (ardhachand)
        'anushtubh_half': [8, 8],      # Half Anushtubh
        'trishtubh_half': [11, 11],    # Half Trishtubh
    }

    # Meter name aliases (for flexible input)
    METER_ALIASES: Dict[str, str] = {
        'गायत्री': 'gayatri',
        'अनुष्टुभ्': 'anushtubh',
        'अनुष्टुप्': 'anushtubh',
        'त्रिष्टुभ्': 'trishtubh',
        'त्रिष्टुप्': 'trishtubh',
        'जगती': 'jagati',
        'जगति': 'jagati',
        'उष्णिक्': 'ushnik',
        'बृहती': 'brihati',
        'पङ्क्ति': 'pankti',
        'वसन्ततिलका': 'vasantatilaka',
        'मन्दाक्रान्ता': 'mandakranta',
        'शार्दूलविक्रीडित': 'shardula_vikridita',
        'स्रग्धरा': 'sragdhara',
        'shloka': 'anushtubh',
        'sloka': 'anushtubh',
        'श्लोक': 'anushtubh',
    }

    # Sanskrit/Devanagari vowels for syllable counting
    # Independent vowels
    DEVANAGARI_VOWELS = 'अआइईउऊऋॠऌॡएऐओऔ'
    # Dependent vowels (mātrās)
    DEVANAGARI_MATRAS = 'ािीुूृॄॢॣेैोौ'

    # IAST/transliteration vowels (including long vowels with macrons)
    IAST_VOWELS = 'aāiīuūṛṝḷḹeaioau'
    IAST_VOWELS_PATTERN = r'[aāiīuūṛṝḷḹeo]|ai|au'

    # SLP1 vowels
    SLP1_VOWELS = 'aAiIuUfFxXeEoO'

    def __init__(self, data_path: Optional[str] = None):
        """
        Initialize the pada splitter with optional CSV data loading.
        
        Args:
            data_path: Path to the data directory containing CSV files.
                       If None, uses default relative path.
        """
        # Viṣamavṛtta patterns: meter_name -> {pada_num: {syllables: int, pattern: str, gana: str}}
        self.vishama_patterns: Dict[str, Dict[int, Dict]] = {}

        # Ardhasama patterns: meter_name -> {pada_num: {syllables: int, pattern: str, gana: str}}
        self.ardhasama_patterns: Dict[str, Dict[int, Dict]] = {}

        # Determine data path
        if data_path:
            self.data_path = Path(data_path)
        else:
            # Default: look for data directory relative to this file
            self.data_path = Path(__file__).parent.parent / 'data'

        # Load CSV data if available
        self._load_csv_meters()

    def _load_csv_meters(self):
        """Load meter patterns from CSV files."""
        # Load Viṣamavṛtta (unequal meters)
        vishama_file = self.data_path / 'chanda_vishama.csv'
        if vishama_file.exists():
            self._load_vishama_csv(vishama_file)

        # Load Ardhasama (half-equal meters)
        ardhasama_file = self.data_path / 'chanda_ardhasama.csv'
        if ardhasama_file.exists():
            self._load_ardhasama_csv(ardhasama_file)

    def _load_vishama_csv(self, filepath: Path):
        """
        Load Viṣamavṛtta patterns from CSV.
        
        CSV format: वृत्त,पद,लक्षण,लक्षण (raw),अक्षरसङ्ख्या,मात्रा,यति
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    meter_name = row.get('वृत्त', '').strip()
                    pada_str = row.get('पद', '').strip()
                    gana = row.get('लक्षण', '').strip()
                    pattern = row.get('लक्षण (raw)', '').strip()
                    syllables_str = row.get('अक्षरसङ्ख्या', '').strip()
                    matra_str = row.get('मात्रा', '').strip()

                    # Skip empty rows
                    if not meter_name or not pada_str or not pattern:
                        continue

                    try:
                        pada_num = int(pada_str)
                        syllables = int(syllables_str) if syllables_str else len(pattern)
                        matras = int(matra_str) if matra_str else 0
                    except ValueError:
                        continue

                    # Initialize meter entry if needed
                    if meter_name not in self.vishama_patterns:
                        self.vishama_patterns[meter_name] = {}

                    # Store pada info
                    self.vishama_patterns[meter_name][pada_num] = {
                        'syllables': syllables,
                        'pattern': pattern,
                        'gana': gana,
                        'matras': matras
                    }

                    # Also add to METERS dict with syllable counts
                    normalized = self._create_meter_key(meter_name)
                    if normalized not in self.METERS:
                        # Will be updated after all padas are loaded
                        pass

            # Update METERS dict with syllable patterns
            for meter_name, padas in self.vishama_patterns.items():
                normalized = self._create_meter_key(meter_name)
                # Sort padas and extract syllable counts
                sorted_padas = sorted(padas.keys())
                syllable_pattern = [padas[p]['syllables'] for p in sorted_padas]
                if syllable_pattern:
                    self.METERS[normalized] = syllable_pattern
                    # Add alias
                    self.METER_ALIASES[meter_name] = normalized

            print(f"[PadaSplitter] Loaded {len(self.vishama_patterns)} Viṣamavṛtta meters")

        except Exception as e:
            print(f"[PadaSplitter] Warning: Could not load Viṣamavṛtta CSV: {e}")

    def _load_ardhasama_csv(self, filepath: Path):
        """
        Load Ardhasama patterns from CSV.
        
        CSV format: वृत्त,पद,लक्षण,लक्षण (raw),अक्षरसङ्ख्या,मात्रा,यति
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    meter_name = row.get('वृत्त', '').strip()
                    pada_str = row.get('पद', '').strip()
                    gana = row.get('लक्षण', '').strip()
                    pattern = row.get('लक्षण (raw)', '').strip()
                    syllables_str = row.get('अक्षरसङ्ख्या', '').strip()
                    matra_str = row.get('मात्रा', '').strip()

                    # Skip empty rows
                    if not meter_name or not pada_str or not pattern:
                        continue

                    try:
                        pada_num = int(pada_str)
                        syllables = int(syllables_str) if syllables_str else len(pattern)
                        matras = int(matra_str) if matra_str else 0
                    except ValueError:
                        continue

                    # Initialize meter entry if needed
                    if meter_name not in self.ardhasama_patterns:
                        self.ardhasama_patterns[meter_name] = {}

                    # Store pada info
                    self.ardhasama_patterns[meter_name][pada_num] = {
                        'syllables': syllables,
                        'pattern': pattern,
                        'gana': gana,
                        'matras': matras
                    }

            # Update METERS dict with syllable patterns
            for meter_name, padas in self.ardhasama_patterns.items():
                normalized = self._create_meter_key(meter_name)
                sorted_padas = sorted(padas.keys())
                syllable_pattern = [padas[p]['syllables'] for p in sorted_padas]
                if syllable_pattern:
                    self.METERS[normalized] = syllable_pattern
                    self.METER_ALIASES[meter_name] = normalized

            print(f"[PadaSplitter] Loaded {len(self.ardhasama_patterns)} Ardhasama meters")

        except Exception as e:
            print(f"[PadaSplitter] Warning: Could not load Ardhasama CSV: {e}")

    def _create_meter_key(self, meter_name: str) -> str:
        """Create a normalized key for the METERS dictionary."""
        # Convert Devanagari to ASCII-safe key
        key = meter_name.lower().replace(' ', '_')
        # For Devanagari names, use transliteration or hash
        if any('\u0900' <= c <= '\u097F' for c in key):
            try:
                key = transliterate(meter_name, sanscript.DEVANAGARI, sanscript.SLP1).lower()
            except Exception:
                key = f"vishama_{hash(meter_name) % 10000}"
        return key

    def get_vishama_pattern(self, meter_name: str, pada_num: int) -> Optional[Dict]:
        """
        Get the pattern for a specific pada of a Viṣamavṛtta meter.
        
        Args:
            meter_name: Name of the meter (Devanagari or romanized)
            pada_num: Pada number (1-4)
            
        Returns:
            Dict with 'syllables', 'pattern', 'gana', 'matras' or None
        """
        # Direct lookup
        if meter_name in self.vishama_patterns:
            return self.vishama_patterns[meter_name].get(pada_num)

        # Try normalized lookup
        normalized = self._normalize_meter_name(meter_name)
        for name, padas in self.vishama_patterns.items():
            if self._create_meter_key(name) == normalized:
                return padas.get(pada_num)

        return None

    def get_ardhasama_pattern(self, meter_name: str, pada_num: int) -> Optional[Dict]:
        """
        Get the pattern for a specific pada of an Ardhasama meter.
        
        Args:
            meter_name: Name of the meter (Devanagari or romanized)
            pada_num: Pada number (1-4)
            
        Returns:
            Dict with 'syllables', 'pattern', 'gana', 'matras' or None
        """
        # Direct lookup
        if meter_name in self.ardhasama_patterns:
            return self.ardhasama_patterns[meter_name].get(pada_num)

        # Try normalized lookup
        normalized = self._normalize_meter_name(meter_name)
        for name, padas in self.ardhasama_patterns.items():
            if self._create_meter_key(name) == normalized:
                return padas.get(pada_num)

        return None

    def is_vishama_meter(self, meter_name: str) -> bool:
        """Check if a meter is a Viṣamavṛtta (unequal pada meter)."""
        if meter_name in self.vishama_patterns:
            return True
        normalized = self._normalize_meter_name(meter_name)
        for name in self.vishama_patterns:
            if self._create_meter_key(name) == normalized:
                return True
        return False

    def is_ardhasama_meter(self, meter_name: str) -> bool:
        """Check if a meter is an Ardhasama (half-equal pada meter)."""
        if meter_name in self.ardhasama_patterns:
            return True
        normalized = self._normalize_meter_name(meter_name)
        for name in self.ardhasama_patterns:
            if self._create_meter_key(name) == normalized:
                return True
        return False

    def get_meter_info(self, meter_name: str) -> Optional[Dict]:
        """
        Get comprehensive information about a meter.
        
        Returns:
            Dict with 'name', 'type', 'total_syllables', 'padas' info
        """
        # Check Viṣamavṛtta
        if meter_name in self.vishama_patterns:
            padas = self.vishama_patterns[meter_name]
            return {
                'name': meter_name,
                'type': 'viṣamavṛtta',
                'total_syllables': sum(p['syllables'] for p in padas.values()),
                'pada_count': len(padas),
                'padas': padas
            }

        # Check Ardhasama
        if meter_name in self.ardhasama_patterns:
            padas = self.ardhasama_patterns[meter_name]
            return {
                'name': meter_name,
                'type': 'ardhasama',
                'total_syllables': sum(p['syllables'] for p in padas.values()),
                'pada_count': len(padas),
                'padas': padas
            }

        # Check standard meters
        normalized = self._normalize_meter_name(meter_name)
        if normalized in self.METERS:
            pattern = self.METERS[normalized]
            return {
                'name': meter_name,
                'type': 'sama' if len(set(pattern)) == 1 else 'mixed',
                'total_syllables': sum(pattern),
                'pada_count': len(pattern),
                'syllable_pattern': pattern
            }

        return None

    def _normalize_meter_name(self, meter: str) -> str:
        """Normalize meter name to internal format"""
        meter_lower = meter.lower().strip()

        # Check aliases first
        if meter in self.METER_ALIASES:
            return self.METER_ALIASES[meter]
        if meter_lower in self.METER_ALIASES:
            return self.METER_ALIASES[meter_lower]

        # Already a valid meter name
        if meter_lower in self.METERS:
            return meter_lower

        return meter_lower

    def _detect_script(self, text: str) -> str:
        """Detect the script of the input text"""
        try:
            detected = detect(text)
            if detected:
                return detected
        except Exception:
            pass

        # Fallback detection
        if any(c in text for c in self.DEVANAGARI_VOWELS + self.DEVANAGARI_MATRAS):
            return sanscript.DEVANAGARI
        elif any(c in text for c in 'āīūṛṝḷḹṃḥṅñṭḍṇśṣ'):
            return sanscript.IAST
        elif any(c in text for c in 'AIUFXEO'):  # SLP1 specific
            return sanscript.SLP1
        else:
            return sanscript.IAST  # Default to IAST for romanized

    def _to_devanagari(self, text: str) -> str:
        """Convert text to Devanagari if not already"""
        script = self._detect_script(text)
        if script == sanscript.DEVANAGARI:
            return text
        try:
            return transliterate(text, script, sanscript.DEVANAGARI)
        except Exception:
            return text

    def count_syllables(self, text: str) -> int:
        """
        Count syllables in Sanskrit text by counting vowels.
        
        In Sanskrit, each syllable (akṣara) contains exactly one vowel sound.
        A syllable can be:
        - An independent vowel (अ, आ, इ, etc.)
        - A consonant + dependent vowel (मा, कि, etc.)
        - A consonant cluster + vowel (स्त्र + vowel)
        
        Args:
            text: Sanskrit text (Devanagari or transliteration)
        
        Returns:
            Number of syllables
        """
        script = self._detect_script(text)

        if script == sanscript.DEVANAGARI:
            return self._count_syllables_devanagari(text)
        else:
            # Convert to Devanagari for consistent counting
            devanagari = self._to_devanagari(text)
            return self._count_syllables_devanagari(devanagari)

    def _count_syllables_devanagari(self, text: str) -> int:
        """
        Count syllables in Devanagari text.
        
        Rules:
        1. Each independent vowel = 1 syllable
        2. Each consonant with inherent 'a' or explicit mātrā = 1 syllable
        3. Consonant with halant (्) = 0 syllables (combines with next)
        4. Anusvara (ं) and visarga (ः) don't add syllables
        5. Special symbols like ॐ (Om) = 1 syllable
        """
        # Remove spaces and punctuation
        text = re.sub(r'[\s।॥,\.!?\d]+', '', text)

        # Handle special symbols first
        # Om (ॐ) is a single syllable
        om_count = text.count('ॐ')
        text = text.replace('ॐ', '')  # Remove Om for further processing

        # Count independent vowels
        independent_vowels = sum(1 for c in text if c in self.DEVANAGARI_VOWELS)

        # Count dependent vowels (mātrās)
        dependent_vowels = sum(1 for c in text if c in self.DEVANAGARI_MATRAS)

        # Count consonants with inherent 'a' (no halant, no mātrā following)
        # A consonant has inherent 'a' if:
        # - It's not followed by halant (्)
        # - It's not followed by a mātrā
        consonant_pattern = r'[क-ह](?![्' + self.DEVANAGARI_MATRAS + '])'
        inherent_a_consonants = len(re.findall(consonant_pattern, text))

        # Handle special cases
        # Avagraha (ऽ) represents elided 'a' - counts as syllable
        avagraha_count = text.count('ऽ')

        total = independent_vowels + dependent_vowels + inherent_a_consonants + avagraha_count + om_count

        return total

    def get_syllables_with_positions(self, text: str) -> List[Tuple[str, int, int]]:
        """
        Get syllables with their character positions in the original text.
        
        Returns:
            List of (syllable_text, start_pos, end_pos) tuples
        """
        # Convert to Devanagari for processing
        devanagari = self._to_devanagari(text)

        syllables = []
        current_syllable = ""
        start_pos = 0

        i = 0
        while i < len(devanagari):
            char = devanagari[i]

            # Skip whitespace and punctuation
            if char in ' \t\n।॥,।':
                if current_syllable:
                    syllables.append((current_syllable, start_pos, i))
                    current_syllable = ""
                i += 1
                continue

            # Independent vowel starts a new syllable
            if char in self.DEVANAGARI_VOWELS:
                if current_syllable:
                    syllables.append((current_syllable, start_pos, i))
                start_pos = i
                current_syllable = char
                i += 1
                # Include any following nasalization or visarga
                while i < len(devanagari) and devanagari[i] in 'ंःँ':
                    current_syllable += devanagari[i]
                    i += 1
                syllables.append((current_syllable, start_pos, i))
                current_syllable = ""
                continue

            # Consonant
            if '\u0915' <= char <= '\u0939':  # क to ह
                if current_syllable:
                    # Check if previous syllable is complete
                    # (has a vowel or ends without halant)
                    if any(c in self.DEVANAGARI_MATRAS + self.DEVANAGARI_VOWELS for c in current_syllable) or \
                       (current_syllable and current_syllable[-1] not in '्'):
                        syllables.append((current_syllable, start_pos, i))
                        start_pos = i
                        current_syllable = ""

                if not current_syllable:
                    start_pos = i

                current_syllable += char
                i += 1

                # Consume any following halants and consonants (conjuncts)
                while i < len(devanagari):
                    if devanagari[i] == '्':  # Halant
                        current_syllable += devanagari[i]
                        i += 1
                        # Next should be a consonant in a conjunct
                        if i < len(devanagari) and '\u0915' <= devanagari[i] <= '\u0939':
                            current_syllable += devanagari[i]
                            i += 1
                        else:
                            break
                    elif devanagari[i] in self.DEVANAGARI_MATRAS:
                        # Mātrā completes the syllable
                        current_syllable += devanagari[i]
                        i += 1
                        # Include any following anusvara/visarga
                        while i < len(devanagari) and devanagari[i] in 'ंःँ':
                            current_syllable += devanagari[i]
                            i += 1
                        break
                    elif devanagari[i] in 'ंःँ':
                        # Anusvara/visarga on inherent 'a'
                        current_syllable += devanagari[i]
                        i += 1
                    else:
                        break

                continue

            # Other characters (nukta, etc.)
            if current_syllable:
                current_syllable += char
            i += 1

        # Don't forget the last syllable
        if current_syllable:
            syllables.append((current_syllable, start_pos, len(devanagari)))

        return syllables

    def split_verse(
        self,
        text: str,
        meter: Optional[str] = None,
        pattern: Optional[List[int]] = None
    ) -> SplitResult:
        """
        Split a Sanskrit verse into padas based on the specified meter or pattern.
        
        Args:
            text: Sanskrit verse (Devanagari or transliteration)
            meter: Name of the meter (e.g., 'anushtubh', 'trishtubh')
            pattern: Custom pattern as list of syllable counts per pada
                    (e.g., [8, 8, 8, 8] for anushtubh)
        
        Returns:
            SplitResult object containing the padas and metadata
        
        Raises:
            ValueError: If neither meter nor pattern is provided
        """
        if meter is None and pattern is None:
            raise ValueError("Either 'meter' or 'pattern' must be provided")

        # Get the pattern
        if pattern is not None:
            meter_pattern = pattern
            meter_name = "custom"
        else:
            meter_name = self._normalize_meter_name(meter)
            if meter_name not in self.METERS:
                return SplitResult(
                    original_text=text,
                    meter=meter,
                    meter_pattern=[],
                    padas=[],
                    total_syllables=self.count_syllables(text),
                    success=False,
                    message=f"Unknown meter: {meter}. Available: {', '.join(self.METERS.keys())}"
                )
            meter_pattern = self.METERS[meter_name]

        # Convert to Devanagari for processing
        original_text = text
        devanagari = self._to_devanagari(text)

        # Count total syllables
        total_syllables = self.count_syllables(devanagari)
        expected_syllables = sum(meter_pattern)

        # Check if syllable count matches
        if abs(total_syllables - expected_syllables) > 2:
            return SplitResult(
                original_text=original_text,
                meter=meter_name,
                meter_pattern=meter_pattern,
                padas=[],
                total_syllables=total_syllables,
                success=False,
                message=f"Syllable count mismatch: found {total_syllables}, expected {expected_syllables} for {meter_name}"
            )

        # Split into padas
        padas = self._split_into_padas(devanagari, meter_pattern)

        return SplitResult(
            original_text=original_text,
            meter=meter_name,
            meter_pattern=meter_pattern,
            padas=padas,
            total_syllables=total_syllables,
            success=True,
            message="Successfully split verse into padas"
        )

    def _split_into_padas(self, text: str, pattern: List[int]) -> List[Pada]:
        """
        Split text into padas according to the syllable pattern.
        Preserves whole words when possible.
        
        Args:
            text: Sanskrit text in Devanagari
            pattern: List of syllable counts per pada
        
        Returns:
            List of Pada objects
        """
        # Tokenize into words
        words = self._tokenize_words(text)

        # Get syllable count for each word
        word_syllables = [(word, self.count_syllables(word)) for word in words]

        padas = []
        current_word_idx = 0

        for pada_num, target_syllables in enumerate(pattern, 1):
            pada_text = ""
            pada_syllable_count = 0

            while current_word_idx < len(word_syllables) and pada_syllable_count < target_syllables:
                word, syllables = word_syllables[current_word_idx]

                if pada_syllable_count + syllables <= target_syllables:
                    # Whole word fits in this pada
                    if pada_text:
                        pada_text += " "
                    pada_text += word
                    pada_syllable_count += syllables
                    current_word_idx += 1
                else:
                    # Need to split this word
                    syllables_needed = target_syllables - pada_syllable_count

                    if syllables_needed > 0:
                        # Split the word at the syllable boundary
                        first_part, remaining_part = self._split_word_at_syllable(
                            word, syllables_needed
                        )

                        if pada_text:
                            pada_text += " "
                        pada_text += first_part
                        pada_syllable_count += syllables_needed

                        # Update the word list with the remaining part
                        remaining_syllables = syllables - syllables_needed
                        word_syllables[current_word_idx] = (remaining_part, remaining_syllables)
                    break

            padas.append(Pada(
                text=pada_text.strip(),
                syllable_count=pada_syllable_count,
                position=pada_num
            ))

        return padas

    def _tokenize_words(self, text: str) -> List[str]:
        """
        Tokenize Sanskrit text into words.
        Preserves daṇḍas (।) and double daṇḍas (॥) as separate tokens.
        """
        # Split on whitespace and punctuation, keeping words
        text = text.strip()

        # Replace daṇḍas with spaces temporarily
        text = re.sub(r'[।॥]+', ' ', text)

        # Split on whitespace
        words = text.split()

        # Filter empty strings
        words = [w.strip() for w in words if w.strip()]

        return words

    def _split_word_at_syllable(self, word: str, syllable_count: int) -> Tuple[str, str]:
        """
        Split a word at a specific syllable boundary.
        
        Args:
            word: The word to split (Devanagari)
            syllable_count: Number of syllables in the first part
        
        Returns:
            Tuple of (first_part, remaining_part)
        """
        if syllable_count <= 0:
            return ("", word)

        syllables = self._get_syllable_boundaries(word)

        if syllable_count >= len(syllables):
            return (word, "")

        # Find the character position at the syllable boundary
        split_pos = syllables[syllable_count - 1][1]

        first_part = word[:split_pos]
        remaining_part = word[split_pos:]

        return (first_part, remaining_part)

    def _get_syllable_boundaries(self, word: str) -> List[Tuple[int, int]]:
        """
        Get the character boundaries of each syllable in a word.
        
        Returns:
            List of (start, end) tuples for each syllable
        """
        boundaries = []
        i = 0
        start = 0

        while i < len(word):
            char = word[i]

            # Independent vowel
            if char in self.DEVANAGARI_VOWELS:
                start = i
                i += 1
                # Include following anusvara/visarga
                while i < len(word) and word[i] in 'ंःँ':
                    i += 1
                boundaries.append((start, i))
                start = i
                continue

            # Consonant
            if '\u0915' <= char <= '\u0939':
                if i == start:
                    start = i

                i += 1

                # Process consonant clusters and mātrās
                while i < len(word):
                    if word[i] == '्':  # Halant
                        i += 1
                        if i < len(word) and '\u0915' <= word[i] <= '\u0939':
                            i += 1
                        else:
                            break
                    elif word[i] in self.DEVANAGARI_MATRAS:
                        i += 1
                        while i < len(word) and word[i] in 'ंःँ':
                            i += 1
                        break
                    elif word[i] in 'ंःँ':
                        i += 1
                    else:
                        break

                boundaries.append((start, i))
                start = i
                continue

            # Other characters
            i += 1

        return boundaries

    def auto_split(self, text: str) -> SplitResult:
        """
        Automatically detect the meter and split the verse.
        
        Args:
            text: Sanskrit verse
        
        Returns:
            SplitResult with the best matching meter
        """
        total_syllables = self.count_syllables(text)

        # Try to find a matching meter
        best_meter = None
        best_diff = float('inf')

        for meter_name, pattern in self.METERS.items():
            expected = sum(pattern)
            diff = abs(total_syllables - expected)

            if diff < best_diff:
                best_diff = diff
                best_meter = meter_name

        if best_meter and best_diff <= 2:
            return self.split_verse(text, meter=best_meter)
        else:
            # Try to infer pattern from syllable count
            # Assume 4 equal padas
            if total_syllables % 4 == 0:
                pada_length = total_syllables // 4
                return self.split_verse(text, pattern=[pada_length] * 4)
            elif total_syllables % 3 == 0:
                pada_length = total_syllables // 3
                return self.split_verse(text, pattern=[pada_length] * 3)
            else:
                return SplitResult(
                    original_text=text,
                    meter="unknown",
                    meter_pattern=[],
                    padas=[],
                    total_syllables=total_syllables,
                    success=False,
                    message=f"Could not determine meter for {total_syllables} syllables"
                )

    def get_available_meters(self) -> Dict[str, List[int]]:
        """Return all available meters and their patterns"""
        return self.METERS.copy()


# =============================================================================
# CLI Interface
# =============================================================================

def main():
    """Command-line interface for pada splitting"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Split Sanskrit verses into padas based on chandas patterns'
    )
    parser.add_argument(
        'text',
        nargs='?',
        help='Sanskrit verse to split (Devanagari or transliteration)'
    )
    parser.add_argument(
        '-m', '--meter',
        default='anushtubh',
        help='Meter name (default: anushtubh)'
    )
    parser.add_argument(
        '-p', '--pattern',
        help='Custom pattern as comma-separated integers (e.g., "8,8,8,8")'
    )
    parser.add_argument(
        '-a', '--auto',
        action='store_true',
        help='Auto-detect meter'
    )
    parser.add_argument(
        '-l', '--list-meters',
        action='store_true',
        help='List available meters'
    )
    parser.add_argument(
        '-c', '--count-only',
        action='store_true',
        help='Only count syllables, do not split'
    )

    args = parser.parse_args()

    splitter = PadaSplitter()

    # List meters
    if args.list_meters:
        print("Available meters:")
        print("-" * 50)
        for name, pattern in splitter.get_available_meters().items():
            total = sum(pattern)
            print(f"  {name:20s}: {'-'.join(map(str, pattern)):15s} ({total} syllables)")
        return

    # Need text for other operations
    if not args.text:
        # Interactive mode
        print("Enter Sanskrit verse (Ctrl+D to finish):")
        import sys
        text = sys.stdin.read().strip()
    else:
        text = args.text

    if not text:
        print("Error: No text provided")
        return

    # Count only
    if args.count_only:
        count = splitter.count_syllables(text)
        print(f"Syllable count: {count}")
        return

    # Parse custom pattern
    pattern = None
    if args.pattern:
        try:
            pattern = [int(x.strip()) for x in args.pattern.split(',')]
        except ValueError:
            print(f"Error: Invalid pattern '{args.pattern}'. Use comma-separated integers.")
            return

    # Split the verse
    if args.auto:
        result = splitter.auto_split(text)
    elif pattern:
        result = splitter.split_verse(text, pattern=pattern)
    else:
        result = splitter.split_verse(text, meter=args.meter)

    # Display result
    print("\n" + "=" * 60)
    print("PADA SPLIT RESULT")
    print("=" * 60)
    print(f"\nOriginal: {result.original_text}")
    print(f"\n{result}")

    if not result.success:
        print(f"\n⚠️  {result.message}")
    else:
        print(f"\n✓ {result.message}")


if __name__ == '__main__':
    main()
