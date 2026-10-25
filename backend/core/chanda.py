#!/usr/bin/env python3
"""
Chanda: the Sanskrit meter identification engine.

The class is assembled from mixins, one module each:
chanda_tables (meter tables), chanda_syllables, chanda_input,
chanda_names, chanda_matching, chanda_structure, chanda_data,
chanda_vedic, chanda_vedic_patterns and chanda_format.
chanda_line holds identify_line and chanda_verse the verse-level scoring.
This module keeps the constructor, identify_from_text and identify_with_sandhi.
"""

import os
import re
from collections import defaultdict

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

from .chanda_constants import (
    ICU_AVAILABLE,
    VEDIC_MAPPINGS_AVAILABLE,
)
from .chanda_data import MeterDataMixin
from .chanda_format import ResultFormatMixin
from .chanda_input import InputCheckMixin
from .chanda_line import LineIdentificationMixin
from .chanda_matching import PatternMatchMixin
from .chanda_names import MeterNameMixin
from .chanda_structure import VerseStructureMixin
from .chanda_syllables import SyllableMixin
from .chanda_tables import MeterTables
from .chanda_vedic import VedicMixin
from .chanda_vedic_patterns import VedicPatternMixin
from .chanda_verse import VerseScoringMixin

# Re-exported for callers that check optional ICU support
__all__ = ["Chanda", "ICU_AVAILABLE", "VEDIC_MAPPINGS_AVAILABLE"]


class Chanda(
    ResultFormatMixin,
    VedicPatternMixin,
    VedicMixin,
    MeterDataMixin,
    VerseStructureMixin,
    PatternMatchMixin,
    MeterNameMixin,
    InputCheckMixin,
    SyllableMixin,
    MeterTables,
    LineIdentificationMixin,
    VerseScoringMixin,
):
    """Chanda Identifier"""

    def __init__(self, data_path, symbols='यरतनभजसमलग', syllabization_method='sanskrit_text'):
        """
        Initialize Chanda identifier

        Args:
            data_path: Path to data directory
            symbols: Gana symbols for input/output
            syllabization_method: 'auto', 'icu', or 'sanskrit_text'
                - 'auto': Use ICU if available, else sanskrit_text
                - 'icu': Force ICU-based syllabization (requires PyICU)
                - 'sanskrit_text': Force original sanskrit_text library (DEFAULT - most accurate)
        """
        self.input_map = dict(zip(symbols, self.SYMBOLS, strict=False))
        self.output_map = dict(zip(self.SYMBOLS, symbols, strict=False))
        self.ttable_in = str.maketrans(self.input_map)
        self.ttable_out = str.maketrans(self.output_map)
        self.gana = self.GANA.copy()
        self.gana_inv = {v: k for k, v in self.gana.items()}

        # Data Path
        self.data_path = data_path

        # Syllabization method selection
        if syllabization_method == 'auto':
            self.syllabization_method = 'icu' if ICU_AVAILABLE else 'sanskrit_text'
        elif syllabization_method == 'icu':
            if not ICU_AVAILABLE:
                raise ImportError(
                    "ICU syllabization requested but PyICU/regex not installed. Install with: pip install PyICU regex"
                )
            self.syllabization_method = 'icu'
        elif syllabization_method == 'sanskrit_text':
            self.syllabization_method = 'sanskrit_text'
        else:
            raise ValueError(
                f"Invalid syllabization_method: {syllabization_method}. Must be 'auto', 'icu', or 'sanskrit_text'"
            )

        # Definitions
        self.CHANDA = defaultdict(list)
        self.SINGLE_CHANDA = defaultdict(list)
        self.MULTI_CHANDA = defaultdict(list)
        self.JAATI = defaultdict(list)
        self.MATRA = defaultdict(list)  # Mātrā-based meters
        self.SPLITS = defaultdict(list)
        self.VEDIC_PADA_PATTERNS = {}  # Store pada-level Vedic patterns
        self.METER_SYNONYMS = {}  # Store meter name variants

        # Store comprehensive meter info for pattern validation display
        # Format: meter_name -> {pattern, syllables, matras, gana, type, padas}
        self.METER_INFO = {}

        # Read Data
        self.read_data()
        self.load_meter_synonyms()

        # Pre-compile regex patterns for performance optimization
        # This avoids recompiling 2800+ patterns on every identify_line call
        self._compiled_patterns = {}
        for pattern in self.CHANDA.keys():
            try:
                self._compiled_patterns[pattern] = re.compile(f'^{pattern}$', re.IGNORECASE)
            except re.error:
                # Skip invalid regex patterns
                pass

    def identify_from_text(
        self, text, verse=False, fuzzy=False, save_path=None, scheme=None, use_sandhi=False, mode='auto'
    ):
        """
        Identify meters from text

        If `verse` is True, treat the input as collection of verses.
        NOTE: Currently assumes 4 lines per verse.
        TODO: Add support for 2 lines per verse too. (i.e. 2 pada in same line)

        Bug #2 Fix: Implements verse-level holistic processing

        Parameters
        ----------
        use_sandhi : bool, optional
            If True, uses automatic sandhi resolution for merged words.
            Default is False.
        """
        # Auto-enable verse mode ONLY if mode explicitly requests it
        # For 'auto' mode, respect the verse parameter as passed by caller
        if mode in ['verse', 'vedic']:
            verse = True
        # Note: mode='auto' no longer overrides verse=False

        line_results = []
        verse_results = []
        pragatha_detected = None  # Will hold Pragātha info if detected

        # =====================================================================
        # VEDIC SINGLE-DANDA HANDLING
        # =====================================================================
        # Vedic verses often have a single danda (।) in the middle to mark
        # a caesura or half-verse boundary, but this should NOT split the verse
        # into separate lines. Only double danda (॥) marks verse end in Vedic.
        #
        # Example: Nasadiya Sukta (RV 10.129.1) is 44 syllables (Triṣṭubh)
        # "नासदासीन्नो सदासीत्तदानीं ... यत् । किमावरीवः ... गभीरम्"
        # Should be treated as ONE verse, not two separate lines.
        # =====================================================================
        if mode in ['vedic', 'auto']:
            text = self._merge_vedic_caesura(text)
        # =====================================================================

        # =====================================================================
        # EARLY VALIDATION - Check ORIGINAL text BEFORE transliteration
        # This catches English/gibberish that would otherwise be transliterated
        # =====================================================================
        is_valid_input, validation_reason = self.is_valid_sanskrit_input(text)
        if not is_valid_input:
            return self._invalid_input_response(text, validation_reason)
        # =====================================================================

        lines, _scheme = self.process_text(text)
        if not scheme:
            scheme = _scheme

        # =====================================================================
        # PRAGĀTHA PRE-DETECTION (before standard processing)
        # =====================================================================
        # Pragātha is a 2-verse compound meter that must be detected BEFORE
        # standard verse-by-verse processing. It spans multiple verses.
        if mode in ['vedic', 'auto'] and len(lines) >= 2:
            # Split into verses (ṛks) for Pragātha detection
            verses = self._split_into_verses(text)

            if len(verses) >= 2:
                is_pragatha, pragatha_info = self._detect_pragatha(verses)
                if is_pragatha:
                    pragatha_detected = pragatha_info

        # Bug #2 Fix: If verse mode, pre-aggregate lines for holistic processing
        if verse:
            # First, get holistic verse-level analysis
            verse_aggregates = []
            for i in range(0, len(lines), 4):
                verse_lines = lines[i : i + 4]
                if verse_lines:
                    holistic_result = self.identify_verse_holistically(verse_lines)
                    verse_aggregates.append({'lines': verse_lines, 'holistic': holistic_result, 'start_idx': i})

        for line in lines:
            if not line:
                continue
            original_line = transliterate(line, sanscript.DEVANAGARI, scheme)

            # Use sandhi resolution if enabled
            if use_sandhi:
                line_result = self.identify_with_sandhi(original_line, fuzzy=fuzzy)
            else:
                line_result = self.identify_line(original_line, fuzzy=fuzzy)

            line_results.append({'line': line, 'result': line_result})

        if verse:
            verse_results = self._score_verses(line_results, verse_aggregates, scheme)
        verse_results = self._apply_vedic_mode(text, mode, verse, line_results, verse_results, scheme)

        results = {
            'line': line_results,
            'verse': verse_results,
            'pragatha': pragatha_detected,  # Pragātha detection info if detected
            'effective_mode': self._effective_mode_used(mode, verse_results),  # The actual mode used
        }
        paths = self._save_results(text, verse, fuzzy, results, save_path)
        return {'result': results, 'path': paths}

    ###########################################################################

    def identify_with_sandhi(self, line, k_candidates=5, k_meters=10, fuzzy=False, lexicon_path=None):
        """
        Identify chandas with automatic sandhi resolution.

        This method generates multiple sandhi-split candidates and identifies
        the chandas for each, returning the best match based on a combined
        score of sandhi plausibility and meter confidence.

        Args:
            line (str): Sanskrit text (may contain merged sandhi)
            k_candidates (int): Number of sandhi candidates to try (default: 5)
            k_meters (int): Number of meter matches per candidate (default: 10)
            fuzzy (bool): Enable fuzzy matching for identification (default: False)
            lexicon_path (str): Path to lexicon file for sandhi scoring (default: None)

        Returns:
            dict: Identification result with additional sandhi information:
                - All standard identify_line() keys
                - 'sandhi_candidates': list of tried candidates with scores
                - 'sandhi_best': the selected candidate info
                - 'sandhi_original': original input line

        Example:
            >>> chanda = Chanda('data/')
            >>> result = chanda.identify_with_sandhi("कर्मण्येवाधिकारस्ते")
            >>> print(result['sandhi_best']['rules'])
            >>> print(result['display_chanda'])
        """
        try:
            from .sandhi_rules import gen_candidates
        except ImportError:
            # Fallback to regular identification if sandhi_rules not available
            result = self.identify_line(line, fuzzy=fuzzy, k=k_meters)
            result['sandhi_available'] = False
            result['sandhi_original'] = line
            return result

        # Set default lexicon path if not provided
        if lexicon_path is None:
            lexicon_path = os.path.join(self.data_path, 'sandhi_lexicon.txt')

        # Generate sandhi candidates
        candidates = gen_candidates(
            line, k=k_candidates, lexicon_path=lexicon_path if os.path.exists(lexicon_path) else None
        )

        # Try identification on each candidate
        candidate_results = []
        for cand_info in candidates:
            cand_text = cand_info['cand']
            sandhi_score = cand_info['score']

            # Identify chandas for this candidate
            id_result = self.identify_line(cand_text, fuzzy=fuzzy, k=k_meters)

            # Calculate combined score
            # Use highest meter confidence if found, otherwise use fuzzy similarity
            if id_result['found'] and id_result.get('confidence_scores'):
                # Get highest confidence from exact matches
                meter_conf = max((conf for conf, _ in id_result['confidence_scores'].values()), default=0.0)
            elif id_result.get('fuzzy') and len(id_result['fuzzy']) > 0:
                # Use top fuzzy match similarity
                meter_conf = id_result['fuzzy'][0]['similarity'] * 10.0  # Scale to ~10
            else:
                meter_conf = 0.0

            # Combined score: weighted average of sandhi and meter confidence
            # Sandhi score typically ranges -2 to 2, meter confidence 0-17
            # Normalize sandhi to 0-10 range, then combine
            normalized_sandhi = ((sandhi_score + 2.0) / 4.0) * 10.0
            combined_score = (0.3 * normalized_sandhi) + (0.7 * meter_conf)

            candidate_results.append(
                {
                    'candidate': cand_text,
                    'sandhi_score': sandhi_score,
                    'sandhi_rules': cand_info['rules'],
                    'meter_confidence': meter_conf,
                    'combined_score': combined_score,
                    'identification': id_result,
                }
            )

        # Sort by combined score and select best
        candidate_results.sort(key=lambda x: x['combined_score'], reverse=True)
        best = candidate_results[0] if candidate_results else None

        if best:
            # Return the identification result of the best candidate
            result = best['identification'].copy()

            # Add sandhi metadata
            result['sandhi_available'] = True
            result['sandhi_original'] = line
            result['sandhi_best'] = {
                'candidate': best['candidate'],
                'sandhi_score': best['sandhi_score'],
                'rules': best['sandhi_rules'],
                'meter_confidence': best['meter_confidence'],
                'combined_score': best['combined_score'],
            }
            result['sandhi_candidates'] = [
                {
                    'candidate': c['candidate'],
                    'sandhi_score': c['sandhi_score'],
                    'rules': c['sandhi_rules'],
                    'combined_score': c['combined_score'],
                }
                for c in candidate_results
            ]
        else:
            # Fallback to regular identification
            result = self.identify_line(line, fuzzy=fuzzy, k=k_meters)
            result['sandhi_available'] = True
            result['sandhi_original'] = line
            result['sandhi_candidates'] = []

        return result

    ###########################################################################


###############################################################################
