"""Meter tables for PadaSplitter: syllables per pada for common meters, and the viṣama and ardhasama patterns read from the meter CSVs.

Mixed into backend.utils.pada_splitter.PadaSplitter, which sets self.data_path and the two pattern dicts before loading."""

import csv
from pathlib import Path
from typing import Dict, List, Optional

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


class PadaMeterCatalog:
    # Standard meter definitions: name -> list of syllable counts per pada
    METERS: Dict[str, List[int]] = {
        # Classical meters
        'gayatri': [6, 6, 6, 6],  # Classical Gayatri (4×6 = 24)
        'gayatri_vedic': [8, 8, 8],  # Vedic Gayatri (3×8 = 24)
        'anushtubh': [8, 8, 8, 8],  # Shloka meter (4×8 = 32)
        'trishtubh': [11, 11, 11, 11],  # Trishtubh (4×11 = 44)
        'jagati': [12, 12, 12, 12],  # Jagati (4×12 = 48)
        # Additional Vedic meters
        'ushnik': [7, 7, 7, 7],  # Ushnik (4×7 = 28)
        'brihati': [9, 9, 9, 9],  # Brihati (4×9 = 36)
        'pankti': [8, 8, 8, 8, 8],  # Pankti (5×8 = 40)
        # Common classical meters with specific pada structures
        'indravajra': [11, 11, 11, 11],  # Same as Trishtubh
        'upendravajra': [11, 11, 11, 11],  # Same pattern
        'vasantatilaka': [14, 14, 14, 14],  # 4×14 = 56
        'mandakranta': [17, 17, 17, 17],  # 4×17 = 68
        'shardula_vikridita': [19, 19, 19, 19],  # 4×19 = 76
        'sragdhara': [21, 21, 21, 21],  # 4×21 = 84
        # Half-verses (ardhachand)
        'anushtubh_half': [8, 8],  # Half Anushtubh
        'trishtubh_half': [11, 11],  # Half Trishtubh
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
                        'matras': matras,
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
                        'matras': matras,
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
        if any('\u0900' <= c <= '\u097f' for c in key):
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
                'padas': padas,
            }

        # Check Ardhasama
        if meter_name in self.ardhasama_patterns:
            padas = self.ardhasama_patterns[meter_name]
            return {
                'name': meter_name,
                'type': 'ardhasama',
                'total_syllables': sum(p['syllables'] for p in padas.values()),
                'pada_count': len(padas),
                'padas': padas,
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
                'syllable_pattern': pattern,
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

    def get_available_meters(self) -> Dict[str, List[int]]:
        """Return all available meters and their patterns"""
        return self.METERS.copy()
