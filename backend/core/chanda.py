#!/usr/bin/env python3
"""
Chanda: the Sanskrit meter identification engine.

The class is assembled from mixins, one module each:
chanda_tables (meter tables), chanda_syllables, chanda_input,
chanda_names, chanda_matching, chanda_structure, chanda_data,
chanda_vedic, chanda_vedic_patterns and chanda_format.
chanda_line holds identify_line. This module keeps the constructor,
identify_from_text and identify_with_sandhi.
"""

import hashlib
import json
import os
import re
from collections import Counter, defaultdict

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

from .chanda_constants import (
    CONFIDENCE_VEDIC_CLASSICAL_MAP,
    ICU_AVAILABLE,
    VEDIC_MAPPINGS_AVAILABLE,
    get_classical_equivalents,
    normalize_vedic_meter,
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
            verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}

            line_count = 0
            ongoing_score = Counter()
            verse_aggregate_idx = 0
            holistic_boost_applied = False

            for line_idx, line_result in enumerate(line_results):
                _result = line_result['result']

                # Bug #2 Fix + ENHANCED: Use holistic verse analysis with structure detection
                # Apply boost once at the start of each verse
                # When structure confirms Vedic meter, use high boost to override pada-level matches
                if not holistic_boost_applied and verse_aggregate_idx < len(verse_aggregates):
                    current_aggregate = verse_aggregates[verse_aggregate_idx]
                    holistic_result = current_aggregate['holistic']

                    if holistic_result['found']:
                        vedic_meter = holistic_result['meter']
                        structure = holistic_result.get('structure', {})
                        vedic_structure_confirmed = structure.get('vedic_structure_confirmed', False)

                        # Check if there's a consistent classical meter across all verse lines
                        verse_start = verse_aggregate_idx * 4
                        verse_end = min(verse_start + 4, len(line_results))
                        num_lines = verse_end - verse_start

                        # ENHANCED: Check for consistent classical meters using MAJORITY RULE
                        # A classical meter wins over Vedic if it has EXACT pattern matches
                        # in at least 3 out of 4 lines (majority rule)
                        #
                        # This handles:
                        # - True sama classical meters (Indravajrā with same pattern in all lines)
                        # - Upajāti (Indravajrā/Upendravajrā mix - both exact matches)
                        # - Vedic meters with varied patterns (no consistent exact matches)
                        classical_meters_in_lines = []
                        exact_match_meters_per_line = []  # Only meters with exact pattern match
                        pada_level_meters_found = set()  # Track pada-level meters to suppress

                        for idx in range(verse_start, verse_end):
                            if idx < len(line_results):
                                lr = line_results[idx]['result']
                                confidence_scores = lr.get('confidence_scores', {})

                                if lr.get('found') and lr.get('chanda'):
                                    line_meters = []
                                    exact_meters = []
                                    for c in lr['chanda']:
                                        meter_name = c[0] if isinstance(c, tuple) else c
                                        if meter_name != vedic_meter:
                                            # Check if this is a pada-level meter
                                            if self.is_pada_level_meter(meter_name):
                                                pada_level_meters_found.add(meter_name)
                                            else:
                                                line_meters.append(meter_name)
                                                # Check if it's an EXACT pattern match (confidence >= 9.0)
                                                # Include both true exact (10.0) and regex exact (9.0)
                                                if meter_name in confidence_scores:
                                                    conf, match_type = confidence_scores[meter_name]
                                                    if conf >= 9.0:
                                                        exact_meters.append(meter_name)
                                    classical_meters_in_lines.append(set(line_meters))
                                    exact_match_meters_per_line.append(set(exact_meters))
                                else:
                                    classical_meters_in_lines.append(set())
                                    exact_match_meters_per_line.append(set())

                        # Find classical meters with MAJORITY exact matches (≥3/4 or ≥2/3 lines)
                        has_consistent_classical = False

                        if exact_match_meters_per_line and len(exact_match_meters_per_line) == num_lines:
                            # Count how many lines each meter appears in with exact match
                            meter_counts = {}
                            for line_meters in exact_match_meters_per_line:
                                for meter in line_meters:
                                    meter_counts[meter] = meter_counts.get(meter, 0) + 1

                            # Find meters with majority (≥75%) of lines having exact match
                            threshold = max(3, int(num_lines * 0.75))  # At least 3 out of 4
                            majority_meters = [m for m, count in meter_counts.items() if count >= threshold]

                            if majority_meters:
                                has_consistent_classical = True

                        # ENHANCED: Apply Vedic boost ONLY when:
                        # 1. Structure confirms Vedic meter (4×11, 4×12, etc.), AND
                        # 2. There is NO consistent classical meter (majority exact matches)
                        #
                        # This ensures:
                        # - Triṣṭubh beats vidhvaṅkamālā (no majority exact matches for classical)
                        # - But Indravajrā (majority exact matches) beats Triṣṭubh
                        if vedic_structure_confirmed and not has_consistent_classical:
                            # Structure confirmed (4×11, 4×12, etc.) AND no consistent classical meter:
                            # Apply high boost to Vedic meter to beat pada-level matches
                            ongoing_score[vedic_meter] += 8.0  # Results in ~12.0 total confidence

                            # Suppress pada-level meters from ongoing_score
                            for pada_meter in pada_level_meters_found:
                                if pada_meter in ongoing_score:
                                    # Reduce score significantly but don't remove entirely
                                    # This keeps them as "secondary" matches for display
                                    ongoing_score[pada_meter] *= 0.3
                        elif vedic_structure_confirmed and has_consistent_classical:
                            # Structure matches Vedic but classical meter has majority exact matches
                            # Don't boost Vedic - let classical win
                            pass
                        elif num_lines >= 3 and not has_consistent_classical:
                            # Multiple lines (≥3) but no Vedic structure confirmation
                            # Apply small boost only if no consistent classical
                            ongoing_score[vedic_meter] += 2.0
                        # For single/dual lines (num_lines < 3): Don't boost Vedic at all
                        # Let exact pattern matches determine the meter

                    holistic_boost_applied = True

                if _result['found']:
                    _chanda = _result['chanda']
                    _unique_chanda = list(dict(_chanda))

                    # ENHANCED: Use confidence scores from multi-level matching
                    confidence_scores = _result.get('confidence_scores', {})

                    # =====================================================================
                    # VEDIC-CLASSICAL MAPPING ENRICHMENT (SIH 2025)
                    # For verse-level analysis, enrich confidence scores with empirical mappings
                    # This helps when processing Vedic texts with verse=True parameter
                    # =====================================================================
                    if VEDIC_MAPPINGS_AVAILABLE and holistic_result and holistic_result.get('found'):
                        vedic_meter = holistic_result.get('meter')
                        if vedic_meter:
                            classical_equivalents = get_classical_equivalents(vedic_meter)
                            if classical_equivalents:
                                for equiv_name in classical_equivalents[:3]:
                                    # Check if this equivalent is in current line's predictions
                                    for meter_name in list(confidence_scores.keys()):
                                        normalized_pred = normalize_vedic_meter(meter_name)
                                        normalized_equiv = normalize_vedic_meter(equiv_name)

                                        if normalized_pred == normalized_equiv:
                                            # Boost confidence for empirically validated mapping
                                            current_conf, current_type = confidence_scores[meter_name]
                                            if current_conf < CONFIDENCE_VEDIC_CLASSICAL_MAP:
                                                confidence_scores[meter_name] = (
                                                    CONFIDENCE_VEDIC_CLASSICAL_MAP,
                                                    f'vedic_classical_map_{current_type}',
                                                )
                    # =====================================================================

                    for _c in _unique_chanda:
                        # Get meter name (handle tuple format)
                        meter_name = _c[0] if isinstance(_c, tuple) else _c

                        # Use confidence score if available, otherwise default to 1.0
                        if meter_name in confidence_scores:
                            score = confidence_scores[meter_name][0] / 10.0  # Normalize to 0-1
                        else:
                            score = 1.0

                        ongoing_score[_c] += score
                else:
                    for fuzzy_match in _result['fuzzy']:
                        _chanda = fuzzy_match['chanda']
                        _unique_chanda = list(dict(_chanda))
                        for _c in _unique_chanda:
                            ongoing_score[_c] += fuzzy_match['similarity']

                verse_result['lines'].append(line_idx)
                line_count += 1
                if line_count % 4 == 0 or line_idx == len(line_results) - 1:
                    verse_scores = ongoing_score.most_common()
                    if verse_scores:
                        best_score = verse_scores[0][1]
                        tied_meters = [_c for _c, _score in verse_scores if _score == best_score]

                        # Tiebreaker: prefer specific classical meters over generic Vedic ones
                        # Vedic category meters (generic): त्रिष्टुभ्, जगती, गायत्री, अनुष्टुभ्, etc.
                        vedic_category_meters = {'त्रिष्टुभ्', 'जगती', 'गायत्री', 'अनुष्टुभ्', 'उष्णिक्', 'बृहती', 'पङ्क्ति'}

                        # Sort: classical meters first, then Vedic category meters
                        def meter_priority(m):
                            # 0 = classical (preferred), 1 = Vedic category
                            return 1 if m in vedic_category_meters else 0  # noqa: B023 - used before the loop moves on

                        tied_meters.sort(key=meter_priority)
                        best_matches = (tied_meters, best_score)
                    else:
                        best_matches = ([], 0)
                    verse_result['scores'] = verse_scores
                    verse_result['chanda'] = best_matches
                    verse_aggregate_idx += 1
                    holistic_boost_applied = False  # Reset for next verse
                    for _line_idx in verse_result['lines']:
                        line_result = line_results[_line_idx]
                        priority_fuzzy = []
                        existing_fuzzy = line_result['result']['fuzzy']
                        for idx, fuzzy_match in enumerate(existing_fuzzy):
                            if any([(x in best_matches[0]) for x in [c[0] for c in fuzzy_match['chanda']]]):
                                priority_fuzzy.append(existing_fuzzy.pop(idx))
                        line_result['result']['fuzzy'] = priority_fuzzy + existing_fuzzy

                    verse_results.append(verse_result)
                    # reset
                    verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}
                    ongoing_score = Counter()

        # =====================================================================
        # MODAL IDENTIFICATION LOGIC (Auto-Correction with Text Classifier)
        # =====================================================================

        # Use text classifier for smarter auto-detection
        effective_mode = mode
        classifier_confidence = 0.0

        if mode == 'auto' and verse:
            try:
                from .text_classifier import classify_text

                text_class, classifier_confidence = classify_text(text)
                # Use classifier result if confidence is high enough
                if classifier_confidence >= 0.6:
                    effective_mode = text_class  # 'vedic' or 'classical'
            except ImportError:
                # Fallback to old behavior if classifier not available
                pass

        if verse and (effective_mode == 'vedic' or mode == 'vedic'):
            # Run Vedic identification by syllable count
            vedic_mode_result = self._identify_vedic_mode(text)

            should_override = False

            # Check if line-level identification already found a good classical meter
            # If so, don't override with Vedic mode results
            line_has_good_match = False
            line_best_score = 0.0
            for lr in line_results:
                if lr.get('result', {}).get('found'):
                    # Check confidence_scores for high-confidence classical matches
                    conf_scores = lr.get('result', {}).get('confidence_scores', {})
                    for score_info in conf_scores.values():
                        if isinstance(score_info, tuple):
                            score = score_info[0]
                        else:
                            score = score_info
                        if score >= 7.0:  # High confidence (exact match is 10.0)
                            line_has_good_match = True
                            line_best_score = max(line_best_score, score)
                            break
                    if line_has_good_match:
                        break

            if mode == 'vedic':
                # Explicit vedic mode requested - always override
                should_override = True
            elif effective_mode == 'vedic' and not line_has_good_match:
                # Classifier determined vedic, and no good classical match found
                should_override = True
            elif effective_mode == 'vedic' and line_has_good_match:
                # Classifier says vedic but we have a good classical match
                # Only override if Vedic confidence is MUCH higher than line match
                vedic_conf = vedic_mode_result.get('confidence', 0)
                if vedic_conf >= 0.95 and (vedic_conf * 10.0) > (line_best_score + 2.0):
                    should_override = True
                # Otherwise, keep the classical match
            elif mode == 'auto' and effective_mode == 'classical' and vedic_mode_result['meter']:
                # Classifier said classical, but check if Vedic meter is a strong override
                vedic_meter = vedic_mode_result['meter']
                vedic_conf = vedic_mode_result['confidence']

                # Only override if Vedic confidence is very high (unlikely for classical texts)
                if vedic_conf >= 0.95:
                    should_override = True

            if should_override and vedic_mode_result['meter']:
                vm_name = vedic_mode_result['meter']
                vm_score = 10.0 * vedic_mode_result['confidence']

                # Override verse results - collapse into single verse result
                verse_results = [
                    {
                        'chanda': ([vm_name], vm_score),
                        'scheme': scheme,
                        'scores': [(vm_name, vm_score)],
                        'lines': list(range(len(line_results))),
                    }
                ]

                # Update line results to reflect the Vedic meter
                for lr in line_results:
                    # Add to top of chanda list
                    if 'chanda' not in lr['result']:
                        lr['result']['chanda'] = []
                    lr['result']['chanda'].insert(0, (vm_name, ['1-4']))
                    lr['result']['found'] = True

                    # Add to confidence scores
                    if 'confidence_scores' not in lr['result']:
                        lr['result']['confidence_scores'] = {}
                    lr['result']['confidence_scores'][vm_name] = (vm_score, 'vedic_mode')

                    # Update display strings to show the Vedic meter first
                    # This ensures the line-level display matches the verse-level identification
                    formatted_vm = f"{vm_name} [{vm_score:.1f}]"

                    # Update display_chanda_primary
                    if 'display_chanda_primary' in lr['result'] and lr['result']['display_chanda_primary']:
                        lr['result']['display_chanda_primary'] = (
                            f"{formatted_vm} | {lr['result']['display_chanda_primary']}"
                        )
                    else:
                        lr['result']['display_chanda_primary'] = formatted_vm

                    # Update display_chanda
                    if 'display_chanda' in lr['result'] and lr['result']['display_chanda']:
                        lr['result']['display_chanda'] = f"{formatted_vm} / {lr['result']['display_chanda']}"
                    else:
                        lr['result']['display_chanda'] = formatted_vm

        # Determine the effective mode that was used for identification
        # This is important for displaying in the UI when auto-detect is used
        effective_mode_used = mode  # Default to the requested mode
        if mode == 'auto':
            # Check if Vedic override happened
            if verse_results and verse_results[0].get('chanda'):
                verse_meter = verse_results[0]['chanda'][0][0] if verse_results[0]['chanda'][0] else ''
                # Check if the detected meter is Vedic
                vedic_meter_names = [
                    'गायत्री',
                    'त्रिष्टुभ्',
                    'जगती',
                    'अनुष्टुभ्',
                    'पंक्ति',
                    'उष्णिह्',
                    'बृहती',
                    'Gāyatrī',
                    'Triṣṭubh',
                    'Jagatī',
                    'Anuṣṭubh',
                    'Paṅkti',
                    'Uṣṇih',
                    'Bṛhatī',
                ]
                if any(vm.lower() in verse_meter.lower() for vm in vedic_meter_names):
                    effective_mode_used = 'vedic'
                else:
                    effective_mode_used = 'classical'

        results = {
            'line': line_results,
            'verse': verse_results,
            'pragatha': pragatha_detected,  # Pragātha detection info if detected
            'effective_mode': effective_mode_used,  # The actual mode used for identification
        }

        simple_result = []
        if verse:
            for verse_result in verse_results:
                best_matches = " / ".join(verse_result['chanda'][0])
                best_score = verse_result['chanda'][1]
                simple_result.append(f"# {best_matches} ({best_score})")
                simple_result.append("")
                for line_id in verse_result['lines']:
                    line_result = line_results[line_id]
                    simple_result.append(self.format_line_result(line_result['result']))
                simple_result.append("")
        else:
            for line_result in line_results:
                simple_result.append(self.format_line_result(line_result['result']))
                simple_result.append("")

        if save_path is not None:
            os.makedirs(save_path, exist_ok=True)

            md5sum = hashlib.md5(text.encode('utf-8')).hexdigest()
            result_id = f"result_{md5sum}_{int(verse)}_{int(fuzzy)}"

            json_filename = f"{result_id}.json"
            json_path = os.path.join(save_path, json_filename)
            with open(json_path, mode="w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False)

            txt_filename = f"{result_id}.txt"
            txt_path = os.path.join(save_path, txt_filename)
            with open(txt_path, mode="w", encoding="utf-8") as f:
                f.write("\n".join(simple_result))
        else:
            md5sum = None
            json_filename = None
            txt_filename = None

        paths = {'json': json_filename, 'txt': txt_filename}
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
