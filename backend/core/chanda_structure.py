"""Verse structure detection and splitting text into verses and padas.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""

import Levenshtein as Lev

from .chanda_constants import (
    CONFIDENCE_THRESHOLD_HIGH,
    CONFIDENCE_THRESHOLD_MEDIUM,
    MIN_SYLLABLES_FOR_PADA,
    MIN_SYLLABLES_FOR_VERSE,
)


class VerseStructureMixin:
    def detect_verse_structure(self, verse_lines):
        """
        Detect the structural properties of a verse for Vedic meter identification.

        This method analyzes the verse to determine if it matches expected Vedic
        meter structures (4×11 for Triṣṭubh, 4×12 for Jagatī, etc.).

        Args:
            verse_lines: List of verse lines (padas)

        Returns:
            dict with:
                - syllables_per_pada: list of syllable counts per pada
                - total_syllables: total syllable count
                - expected_vedic_meter: detected Vedic meter name (or None)
                - is_sama: True if all padas have equal syllables
                - vedic_structure_confirmed: True if structure matches Vedic expectations
                - pada_similarity_score: 0.0-1.0 score of L-G pattern similarity across padas
                - majority_match_count: number of padas matching the most common pattern
        """
        # Get L-G patterns for each pada
        pada_patterns = []
        syllables_per_pada = []

        for line in verse_lines:
            _, lg_marks = self.mark_lg(line)
            lg_str = ''.join(lg_marks)
            pada_patterns.append(lg_str)
            syllables_per_pada.append(len(lg_str))

        total_syllables = sum(syllables_per_pada)
        num_padas = len(verse_lines)

        # Check if all padas have equal syllables (sama structure)
        is_sama = len(set(syllables_per_pada)) == 1 if syllables_per_pada else False

        # Define expected Vedic meter structures
        vedic_structures = {
            'त्रिष्टुभ्': {'total': 44, 'padas': 4, 'per_pada': 11},
            'जगती': {'total': 48, 'padas': 4, 'per_pada': 12},
            'अनुष्टुभ्': {'total': 32, 'padas': 4, 'per_pada': 8},
            'गायत्री': {'total': 24, 'padas': 3, 'per_pada': 8},
            'उष्णिक्': {'total': 28, 'padas': 4, 'per_pada': 7},
            'बृहती': {'total': 36, 'padas': 4, 'per_pada': 9},
            'पङ्क्ति': {'total': 40, 'padas': 5, 'per_pada': 8},
        }

        # Determine expected Vedic meter based on structure
        expected_vedic_meter = None
        vedic_structure_confirmed = False

        for meter_name, structure in vedic_structures.items():
            # Check total syllable count (allow ±1 tolerance for sandhi/punctuation)
            if abs(total_syllables - structure['total']) <= 1:
                # Check pada count
                if num_padas == structure['padas']:
                    # Check per-pada syllable count (allow ±1 tolerance per pada)
                    pada_matches = sum(1 for s in syllables_per_pada if abs(s - structure['per_pada']) <= 1)
                    # Require at least 3/4 padas to match (majority rule)
                    if pada_matches >= (num_padas * 0.75):
                        expected_vedic_meter = meter_name
                        vedic_structure_confirmed = True
                        break

        # Calculate pada pattern similarity (for Vedic verses, padas should be similar)
        pada_similarity_score = 0.0
        majority_match_count = 0

        if len(pada_patterns) >= 2 and all(len(p) > 0 for p in pada_patterns):
            # Find the most common pada length
            common_length = max(set(syllables_per_pada), key=syllables_per_pada.count)
            matching_padas = [p for p in pada_patterns if len(p) == common_length]

            if len(matching_padas) >= 2:
                # Calculate average pairwise similarity
                total_similarity = 0
                comparisons = 0

                for i, p1 in enumerate(matching_padas):
                    for p2 in matching_padas[i + 1 :]:
                        # Levenshtein distance normalized by length
                        dist = Lev.distance(p1, p2)
                        max_len = max(len(p1), len(p2))
                        similarity = 1.0 - (dist / max_len) if max_len > 0 else 0.0
                        total_similarity += similarity
                        comparisons += 1

                if comparisons > 0:
                    pada_similarity_score = total_similarity / comparisons

            # Count padas matching the first pada pattern (within tolerance)
            if matching_padas:
                reference_pada = matching_padas[0]
                majority_match_count = sum(1 for p in matching_padas if Lev.distance(p, reference_pada) <= 2)

        return {
            'syllables_per_pada': syllables_per_pada,
            'total_syllables': total_syllables,
            'expected_vedic_meter': expected_vedic_meter,
            'is_sama': is_sama,
            'vedic_structure_confirmed': vedic_structure_confirmed,
            'pada_similarity_score': pada_similarity_score,
            'majority_match_count': majority_match_count,
            'num_padas': num_padas,
            'pada_patterns': pada_patterns,
        }

    ###########################################################################
    # Prose Detection (Gadya vs Padya)
    ###########################################################################

    def is_padya(self, lg_pattern, syllable_count, confidence_scores=None):
        """
        Determine if the input text is likely poetry (Padya) or prose (Gadya).

        Sanskrit literature has two forms:
        - Padya (पद्य): Poetry with metrical structure following Chandas
        - Gadya (गद्य): Prose without any metrical constraints

        This method uses multiple heuristics to determine if a given text
        follows a recognizable metrical pattern.

        IMPORTANT: The challenge is that short prose can accidentally match
        metrical patterns. We use STRICT criteria to avoid false positives:
        - Only exact pattern matches are considered "definite poetry"
        - Syllable-count-only matches are treated as "uncertain"
        - Very short texts (< minimum verse length) are marked as uncertain

        Args:
            lg_pattern: L-G pattern string
            syllable_count: Number of syllables in the text
            confidence_scores: Dict of meter_name -> (confidence, match_type)

        Returns:
            tuple: (is_poetry: bool, reason: str, confidence: float)
                - is_poetry: True if text appears to be Padya
                - reason: Explanation for the classification
                - confidence: 0.0-1.0 confidence in the classification
        """
        # Use configured thresholds (defined at module level)

        # Criterion 1: Too few syllables - not enough for any valid meter
        if syllable_count < MIN_SYLLABLES_FOR_PADA:
            return (
                False,
                f"टिप्पणी: केवल {syllable_count} अक्षर - किसी भी छन्द के लिए अपर्याप्त (Too few syllables for any valid meter)",
                0.9,
            )

        # Criterion 2: Check confidence scores for EXACT pattern matches
        if confidence_scores:
            # Get the highest confidence score and its match type
            max_confidence = 0
            best_match_type = ''
            for _meter_name, (conf, match_type) in confidence_scores.items():
                if conf > max_confidence:
                    max_confidence = conf
                    best_match_type = match_type

            # HIGH CONFIDENCE: Exact pattern match (10.0) or exact regex (9.0)
            # These are DEFINITE poetry - the L-G pattern matches a known meter
            if max_confidence >= CONFIDENCE_THRESHOLD_HIGH:
                if best_match_type in ['exact_pattern', 'exact_regex', 'pada_exact_sama']:
                    return True, "उच्च विश्वास के साथ छन्द मिला (High confidence - exact pattern match)", 0.95
                elif best_match_type in ['vedic_syllable_priority', 'vedic_syllable_secondary']:
                    # Vedic by syllable count - only confident if it's a standard verse length
                    if syllable_count in {24, 32, 44, 48}:
                        return True, "वैदिक छन्द अक्षर संख्या से मेल (Vedic meter by syllable count)", 0.85
                    else:
                        return True, "संभावित वैदिक छन्द (Possible Vedic meter)", 0.7

            # MEDIUM CONFIDENCE: Pada-level structural matches
            if max_confidence >= CONFIDENCE_THRESHOLD_MEDIUM:
                if best_match_type in ['pada_similar', 'pada_vedic_sama', 'pada_vedic_similar']:
                    return True, "पाद संरचना से छन्द मिला (Meter matched by pada structure)", 0.8
                else:
                    return True, "मध्यम विश्वास के साथ छन्द मिला (Medium confidence meter match)", 0.7

            # LOW CONFIDENCE: Only syllable-count matches
            # These are UNCERTAIN - prose can accidentally match syllable counts
            if max_confidence >= 5.0 and max_confidence < CONFIDENCE_THRESHOLD_MEDIUM:
                # Be skeptical of syllable-count-only matches, especially for short texts
                if syllable_count < MIN_SYLLABLES_FOR_VERSE:
                    return (
                        False,
                        f"टिप्पणी: केवल अक्षर संख्या से मेल ({syllable_count}) - छोटा पाठ, सम्भवतः गद्य (Only syllable count match - short text, likely prose)",
                        0.6,
                    )
                else:
                    # Longer text with syllable match - uncertain
                    return True, "अक्षर संख्या से संभावित छन्द (Possible meter by syllable count - uncertain)", 0.5

            # VERY LOW CONFIDENCE: Likely prose
            if max_confidence > 0 and max_confidence < 5.0:
                return (
                    False,
                    f"टिप्पणी: न्यून विश्वास ({max_confidence:.1f}) - सम्भवतः गद्य (Low confidence - likely prose)",
                    0.7,
                )

        # No confidence scores available - use structural heuristics

        # Criterion 3: Check for full Vedic meter syllable counts (complete verses)
        vedic_verse_counts = {24, 28, 32, 36, 40, 44, 48}
        if syllable_count in vedic_verse_counts:
            return True, "वैदिक छन्द अक्षर संख्या से मेल - पूर्ण श्लोक (Matches full Vedic verse syllable count)", 0.6

        # Criterion 4: Very short text without exact match - uncertain/prose
        if syllable_count < MIN_SYLLABLES_FOR_VERSE:
            return False, "टिप्पणी: छोटा पाठ, कोई निश्चित छन्द नहीं (Short text without definite meter pattern)", 0.6

        # Criterion 5: Check for standard verse structures
        # 4-pada meters: 32, 44, 48, etc. (must be exact for high confidence)
        if syllable_count >= 24 and syllable_count % 4 == 0:
            pada_length = syllable_count // 4
            if pada_length in {8, 11, 12}:  # Common Vedic pada lengths
                return True, "4-पाद वैदिक संरचना संभव (4-pada Vedic structure possible)", 0.5

        # Criterion 6: Very long text without any match - likely prose
        if syllable_count > 30 and not confidence_scores:
            return (
                False,
                "टिप्पणी: लम्बा पाठ, कोई छन्द प्रतिरूप नहीं - सम्भवतः गद्य (Long text with no meter pattern - likely prose)",
                0.7,
            )

        # Default: Uncertain - mark as uncertain prose
        return False, "टिप्पणी: कोई निश्चित छन्द प्रतिरूप नहीं मिला (No definite meter pattern matched)", 0.5

    ###########################################################################
    # Multi-level Matching System (Priority 2 Enhancement)
    ###########################################################################

    def split_into_padas(self, lg_pattern, num_padas=4):
        """
        Split L-G pattern into equal padas (quarters)

        Args:
            lg_pattern: Full L-G pattern string
            num_padas: Number of padas to split into (default 4)

        Returns:
            List of pada patterns, or None if not evenly divisible
        """
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

    def _split_into_padas(self, text):
        """
        Split Vedic verse text into padas (metrical feet).

        Returns a list of (pada_text, syllable_count) tuples.

        Splitting strategy:
        1. Use explicit pada markers (।, ॥)
        2. If no markers, use line breaks
        3. If still single block, try to infer based on meter structures
        """
        padas = []

        # First try splitting by pada markers
        parts = [p.strip() for p in text.replace('॥', '।').split('।') if p.strip()]

        # If only one part, try line breaks
        if len(parts) == 1:
            parts = [p.strip() for p in text.split('\n') if p.strip()]

        for part in parts:
            clean = part.replace('।', '').replace('॥', '').strip()
            if not clean:
                continue
            _, lg = self.mark_lg(clean)
            padas.append((clean, len(lg)))

        return padas

    def _split_into_vedic_padas(self, verse_text):
        """
        Split a Vedic verse into 2 pādas (not 4 like classical Sanskrit).

        Vedic verses typically have 2 pādas per ṛk (verse unit).

        Returns: list of (pada_text, syllable_count) tuples
        """
        # Clean the verse
        clean_text = verse_text.replace('॥', '।').strip()

        # Try splitting by danda first
        parts = [p.strip() for p in clean_text.split('।') if p.strip()]

        # If we got exactly 2 parts, use them as padas
        if len(parts) == 2:
            padas = []
            for part in parts:
                _, lg = self.mark_lg(part)
                padas.append((part, len(lg)))
            return padas

        # If we got 1 part (no danda), try to split by syllable count heuristic
        # For Pragātha, each verse should have ~23 syllables (11+12)
        if len(parts) == 1:
            text = parts[0]
            _, lg = self.mark_lg(text)
            total_syls = len(lg)

            # If total is in Pragātha range (21-25), try to split at 11
            if 21 <= total_syls <= 25:
                # Split approximately in the middle, favoring 11+12
                # Find word boundary near split point
                syllables, lg_list = self.mark_lg(text)

                # Return as single block if we can't split properly
                return [(text, total_syls)]

        # If we got more than 2 parts, combine appropriately
        if len(parts) > 2:
            # For 4 padas, combine into 2 (typical classical → Vedic conversion)
            if len(parts) == 4:
                pada1 = parts[0] + ' ' + parts[1]
                pada2 = parts[2] + ' ' + parts[3]
                _, lg1 = self.mark_lg(pada1)
                _, lg2 = self.mark_lg(pada2)
                return [(pada1, len(lg1)), (pada2, len(lg2))]
            else:
                # Just return all parts
                padas = []
                for part in parts:
                    _, lg = self.mark_lg(part)
                    padas.append((part, len(lg)))
                return padas

        # Fallback: return as single unit
        if parts:
            _, lg = self.mark_lg(parts[0])
            return [(parts[0], len(lg))]

        return []

    def _split_into_verses(self, text):
        """
        Split text into individual verses (ṛks) using double danda or newlines.

        Returns: list of verse strings
        """
        # First try double danda (॥)
        verses = [v.strip() for v in text.split('॥') if v.strip()]

        # If only one verse, try double pipe (||) or newlines
        if len(verses) == 1:
            verses = [v.strip() for v in text.split('||') if v.strip()]

        if len(verses) == 1:
            # Try splitting by newline pairs (empty line between verses)
            verses = [v.strip() for v in text.split('\n\n') if v.strip()]

        if len(verses) == 1:
            # Finally, try single newlines as verse boundaries
            verses = [v.strip() for v in text.split('\n') if v.strip()]

        return verses

    def _merge_vedic_caesura(self, text):
        """
        Treat single dandas as caesura marks in a one-line Vedic verse.

        When the text has single dandas but no double danda or newline, and
        its syllable count is within 3 of a Vedic total (24, 32, 36, 40, 44
        or 48), return it with the dandas turned into spaces so it is not
        split into separate lines. Otherwise return it unchanged.
        """
        # Check if text has single danda but no double danda
        single_danda_count = text.count('।')
        double_danda_count = text.count('॥')
        newline_count = text.count('\n')

        # If only single dandas and no newlines/double dandas,
        # this might be a Vedic verse with caesura marking
        if single_danda_count >= 1 and double_danda_count == 0 and newline_count == 0:
            # Remove single dandas temporarily and count syllables using chanda engine
            text_no_danda = text.replace('।', ' ').replace('  ', ' ')

            # Use our own syllable counting (more accurate than text_classifier)
            try:
                _, lg_marks = self.mark_lg(text_no_danda)
                # Count non-empty lg marks
                total_syllables = sum(1 for lg in lg_marks if lg)
            except Exception:
                total_syllables = 0

            # Vedic meters: 24 (Gāyatrī), 32 (Anuṣṭubh), 36 (Bṛhatī),
            # 40 (Paṅkti), 44 (Triṣṭubh), 48 (Jagatī)
            vedic_syllable_counts = {24, 32, 36, 40, 44, 48}
            # Also allow ±3 tolerance (Vedic verses can have slight variations)
            is_vedic_count = any(abs(total_syllables - vc) <= 3 for vc in vedic_syllable_counts)

            if is_vedic_count:
                # Replace single dandas with spaces to prevent splitting
                text = text_no_danda
        return text
