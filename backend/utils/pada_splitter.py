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

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .pada_meters import PadaMeterCatalog
from .pada_syllables import PadaSyllables


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
            "---",
        ]
        for pada in self.padas:
            lines.append(str(pada))
        return '\n'.join(lines)


class PadaSplitter(PadaSyllables, PadaMeterCatalog):
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

    def split_verse(self, text: str, meter: Optional[str] = None, pattern: Optional[List[int]] = None) -> SplitResult:
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
                    message=f"Unknown meter: {meter}. Available: {', '.join(self.METERS.keys())}",
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
                message=f"Syllable count mismatch: found {total_syllables}, expected {expected_syllables} for {meter_name}",
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
            message="Successfully split verse into padas",
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
                        first_part, remaining_part = self._split_word_at_syllable(word, syllables_needed)

                        if pada_text:
                            pada_text += " "
                        pada_text += first_part
                        pada_syllable_count += syllables_needed

                        # Update the word list with the remaining part
                        remaining_syllables = syllables - syllables_needed
                        word_syllables[current_word_idx] = (remaining_part, remaining_syllables)
                    break

            padas.append(Pada(text=pada_text.strip(), syllable_count=pada_syllable_count, position=pada_num))

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
                    message=f"Could not determine meter for {total_syllables} syllables",
                )


# =============================================================================
# CLI Interface
# =============================================================================


def main():
    """Command-line interface for pada splitting"""
    import argparse

    parser = argparse.ArgumentParser(description='Split Sanskrit verses into padas based on chandas patterns')
    parser.add_argument('text', nargs='?', help='Sanskrit verse to split (Devanagari or transliteration)')
    parser.add_argument('-m', '--meter', default='anushtubh', help='Meter name (default: anushtubh)')
    parser.add_argument('-p', '--pattern', help='Custom pattern as comma-separated integers (e.g., "8,8,8,8")')
    parser.add_argument('-a', '--auto', action='store_true', help='Auto-detect meter')
    parser.add_argument('-l', '--list-meters', action='store_true', help='List available meters')
    parser.add_argument('-c', '--count-only', action='store_true', help='Only count syllables, do not split')

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
