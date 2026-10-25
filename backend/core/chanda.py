#!/usr/bin/env python3
"""
Chanda: the Sanskrit meter identification engine.

The class is assembled from mixins, one module each:
chanda_tables (meter tables), chanda_syllables, chanda_input,
chanda_names, chanda_matching, chanda_structure, chanda_data,
chanda_vedic, chanda_vedic_patterns and chanda_format.
This module keeps the constructor and the public identify_* entry points.
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
from .chanda_matching import PatternMatchMixin
from .chanda_names import MeterNameMixin
from .chanda_structure import VerseStructureMixin
from .chanda_syllables import SyllableMixin
from .chanda_tables import MeterTables
from .chanda_vedic import VedicMixin
from .chanda_vedic_patterns import VedicPatternMixin
from .confidence_reasons import build_confidence_reasons, get_primary_confidence_reason

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
        # =====================================================================

        # =====================================================================
        # EARLY VALIDATION - Check ORIGINAL text BEFORE transliteration
        # This catches English/gibberish that would otherwise be transliterated
        # =====================================================================
        is_valid_input, validation_reason = self.is_valid_sanskrit_input(text)
        if not is_valid_input:
            # Return early with invalid input result
            invalid_result = {
                'found': False,
                'is_padya': False,
                'is_valid_input': False,
                'validation_error': validation_reason,
                'padya_reason': validation_reason,
                'padya_confidence': 0.0,
                'prose_message': f"अमान्य आदान: {validation_reason} (Invalid input: {validation_reason})",
                'syllables': [],
                'lg': [],
                'gana': '',
                'length': 0,
                'matra': 0,
                'chanda': [],
                'jaati': [],
                'display_scheme': None,
                'display_line': text,
                'display_syllables': [],
                'display_lg': [],
                'display_gana': '',
                'display_length': 0,
                'display_matra': 0,
                'display_chanda': '',
                'display_chanda_primary': '',
                'display_chanda_alternate': '',
                'display_chanda_alternate_count': 0,
                'display_chanda_hidden_count': 0,
                'display_jaati': '',
                'fuzzy': [],
                'confidence_scores': {},
            }
            # Return a structure that matches expected output format
            return {
                'result': {'line': [{'line': text, 'result': invalid_result}], 'verse': [], 'pragatha': None},
                'path': None,
            }
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

    # ----------------------------------------------------------------------- #

    def identify_line(self, line, fuzzy=False, k=10):
        """
        Identify Chanda if possible from a single text line

        @return:
            - answer: dictionary containing scansion details about the line
                - found: boolean indicating if the Chanda was found or not
                - ...
        """

        # =====================================================================
        # INPUT VALIDATION - Reject non-Sanskrit/gibberish text
        # =====================================================================
        is_valid_input, validation_reason = self.is_valid_sanskrit_input(line)
        if not is_valid_input:
            return {
                'found': False,
                'is_padya': False,
                'is_valid_input': False,
                'validation_error': validation_reason,
                'padya_reason': validation_reason,
                'padya_confidence': 0.0,
                'prose_message': f"अमान्य आदान: {validation_reason} (Invalid input: {validation_reason})",
                'syllables': [],
                'lg': [],
                'gana': '',
                'length': 0,
                'matra': 0,
                'chanda': [],
                'jaati': [],
                'display_scheme': None,
                'display_line': line,
                'display_syllables': [],
                'display_lg': [],
                'display_gana': '',
                'display_length': 0,
                'display_matra': 0,
                'display_chanda': '',
                'display_chanda_primary': '',
                'display_chanda_alternate': '',
                'display_chanda_alternate_count': 0,
                'display_chanda_hidden_count': 0,
                'display_jaati': '',
                'fuzzy': [],
                'confidence_scores': {},
            }
        # =====================================================================

        lines, scheme = self.process_text(line)
        output_scheme = scheme if scheme != sanscript.DEVANAGARI else None

        # If input had no actual newlines but got split by dandas (। ॥),
        # join them back together for single-line identification
        # This allows users to input "text1। text2॥" as a single verse
        original_has_newlines = '\n' in line or '\r' in line
        if len(lines) > 1 and not original_has_newlines:
            # Join danda-split segments back into one line for analysis
            line = ' '.join(lines)
        elif len(lines) > 1:
            raise ValueError('Input contains more than one line.')
        elif len(lines) == 1:
            line = lines[0]
        else:
            # Empty input
            return {}

        answer = {}

        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            # lg_str is empty
            return answer

        found = direct_match['found'] or multi_match['found']

        lg_str = ''.join(direct_match['lg'])

        # =====================================================================
        # VEDIC METER PRIORITY CHECK - Added for SIH 2025
        # =====================================================================
        # The 7 major Vedic meters are identified by syllable count, not L-G pattern.
        # HOWEVER: If there's an EXACT pattern match for a classical meter (like
        # Indravajra, Upendravajra, etc.), that should take priority because
        # classical meters have specific L-G patterns, not just syllable counts.
        #
        # Syllable counts: Gayatri(24), Ushnik(28), Anushtubh(32), Brihati(36),
        #                  Pankti(40), Trishtubh(44), Jagati(48)
        #
        # Strategy: Set vedic_priority_meter here, but ONLY add it to confidence_map
        # if there are NO exact pattern matches found later.
        # =====================================================================
        vedic_priority_meter = None
        vedic_priority_confidence = 0.0

        # Check if this verse matches a Vedic meter by syllable count
        # NOTE: Only include meters that make sense for SINGLE-LINE identification.
        # Nicṛt Gāyatrī (21) and Bhurik Gāyatrī (27) are 3-pada verse meters,
        # not single-line meters. A 21-syllable single line is more likely
        # Sragdharā (21 per pada) than Nicṛt Gāyatrī (3×7 verse).
        syllable_count = len(lg_str)
        vedic_syllable_counts = {
            # Only meters where syllable count = single pada OR full verse with 4 padas
            24: 'गायत्री',  # Standard Gāyatrī - 3×8 (also valid as single input)
            28: 'उष्णिक्',  # Uṣṇik - 4×7
            32: 'अनुष्टुभ्',  # Anuṣṭubh - 4×8
            36: 'बृहती',  # Bṛhatī - 4×9
            40: 'पङ्क्ति',  # Paṅkti - 5×8
            44: 'त्रिष्टुभ्',  # Triṣṭubh - 4×11
            48: 'जगती',  # Jagatī - 4×12
            # NOT included: 21 (Nicṛt Gāyatrī) - conflicts with Sragdharā pada
            # NOT included: 27 (Bhurik Gāyatrī) - needs 3-pada verse structure
        }

        if syllable_count in vedic_syllable_counts:
            vedic_priority_meter = vedic_syllable_counts[syllable_count]
            vedic_priority_confidence = 11.0  # Will be used as fallback
            found = True  # Ensure we mark as found
        # NOTE: Vedic range matching moved to AFTER pattern matching check
        # This ensures classical meters with specific L-G patterns take priority
        # =====================================================================

        # Use pre-compiled regex patterns for massive performance boost
        # Previously: ~40ms per verse, Now: ~0.2ms per verse
        regex_matches = [k for k, compiled_re in self._compiled_patterns.items() if compiled_re.match(lg_str)]

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
                chanda += direct_match['chanda']
                jaati += direct_match['jaati']
                gana += direct_match['gana']
                length += direct_match['length']
                matra += direct_match['matra']
            if multi_match['found']:
                chanda += multi_match['chanda']
                jaati += multi_match['jaati']
                gana += multi_match['gana']
                length += multi_match['length']
                matra += multi_match['matra']

            if is_regex_match:
                chanda += [c for m in regex_matches for c in self.CHANDA.get(m) if c not in chanda]

        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI[-1])

        # IMPROVED: Tiered matching - exact pattern matches beat Vedic syllable-count
        # Key insight: Classical meters with specific L-G patterns should win over
        # generic Vedic syllable-count identification.
        # Priority: exact_pattern (10.0) > vedic_fallback (9.5) > exact_regex (9.0) > heuristics

        confidence_map = {}  # meter_name -> (confidence, match_type)

        # TIER 1a: TRUE exact pattern matches (HIGHEST priority - 10.0)
        # These are classical meters with specific L-G patterns like Indravajra
        true_exact_matches = set()
        if direct_match.get('exact_chanda'):
            for c in direct_match['exact_chanda']:
                meter_name = c[0] if isinstance(c, tuple) else c
                true_exact_matches.add(meter_name)
                confidence_map[meter_name] = (10.0, 'exact_pattern')
        if multi_match.get('exact_chanda'):
            for c in multi_match['exact_chanda']:
                meter_name = c[0] if isinstance(c, tuple) else c
                true_exact_matches.add(meter_name)
                confidence_map[meter_name] = (10.0, 'exact_pattern')

        # TIER 1b: Regex pattern matches (slightly lower priority - 9.0)
        regex_pattern_matches = set()
        for pattern_key in regex_matches:
            has_wildcards = any(c.islower() for c in pattern_key if c in 'lg')
            for c in self.CHANDA.get(pattern_key, []):
                meter_name = c[0] if isinstance(c, tuple) else c
                if meter_name not in true_exact_matches:
                    regex_pattern_matches.add(meter_name)
                    if has_wildcards:
                        if meter_name not in confidence_map or confidence_map[meter_name][0] < 9.0:
                            confidence_map[meter_name] = (9.0, 'exact_regex')
                    else:
                        true_exact_matches.add(meter_name)
                        if meter_name not in confidence_map or confidence_map[meter_name][0] < 10.0:
                            confidence_map[meter_name] = (10.0, 'exact_pattern')

        # =====================================================================
        # TIER 1c: VEDIC METER (as FALLBACK when no exact pattern matches)
        # =====================================================================
        # Only add Vedic meter if:
        # 1. No exact pattern matches were found, OR
        # 2. The only exact match IS the Vedic meter itself (e.g., Anushtubh pattern)
        #
        # This ensures Indravajra (exact pattern) beats Trishtubh (syllable count)
        # but Anushtubh still works when there's no other pattern match.
        # =====================================================================
        has_non_vedic_exact_match = (
            bool(true_exact_matches - {vedic_priority_meter}) if vedic_priority_meter else bool(true_exact_matches)
        )

        if vedic_priority_meter:
            if has_non_vedic_exact_match:
                # There are exact pattern matches for classical meters
                # Add Vedic meter as secondary option with lower confidence
                confidence_map[vedic_priority_meter] = (9.5, 'vedic_syllable_secondary')
                vedic_tuple = (vedic_priority_meter, ('',))
                if vedic_tuple not in chanda:
                    chanda.append(vedic_tuple)  # Append, not insert
            else:
                # No exact pattern matches - Vedic meter is primary
                confidence_map[vedic_priority_meter] = (vedic_priority_confidence, 'vedic_syllable_priority')
                vedic_tuple = (vedic_priority_meter, ('',))
                if vedic_tuple not in chanda:
                    chanda.insert(0, vedic_tuple)
        # =====================================================================

        # Combine all exact matches

        # CRITICAL: If we have TRUE exact pattern matches, use ONLY those
        # Plus include Vedic meter as secondary option
        if true_exact_matches:
            chanda = [
                c
                for c in chanda
                if (c[0] if isinstance(c, tuple) else c) in true_exact_matches
                or (c[0] if isinstance(c, tuple) else c) == vedic_priority_meter
            ]
            found = True
        elif regex_pattern_matches:
            # Fall back to regex matches
            # BUT also include Vedic priority meter if present
            chanda = [
                c
                for c in chanda
                if (c[0] if isinstance(c, tuple) else c) in regex_pattern_matches
                or (c[0] if isinstance(c, tuple) else c) == vedic_priority_meter
            ]
            # Ensure Vedic priority meter is in the list
            if vedic_priority_meter:
                vedic_tuple = (vedic_priority_meter, ('',))
                if vedic_tuple not in chanda:
                    chanda.insert(0, vedic_tuple)
            found = True
        else:
            # TIER 2: No exact matches - use multi-level heuristics
            multi_level_matches = self.match_with_confidence(lg_str, fuzzy=fuzzy, max_fuzzy=k)

            # Separate by match type - prioritize better heuristics
            pada_matches = []  # Pada-level structural matches
            syllable_matches = []  # Pure syllable count matches
            fuzzy_matches = []  # Fuzzy Levenshtein matches

            for match_item, confidence, match_type in multi_level_matches:
                if isinstance(match_item, tuple):
                    meter_name = match_item[0]
                    meter_tuple = match_item
                else:
                    meter_name = match_item
                    meter_tuple = (match_item, ('',))

                if match_type in ['pada_sama', 'pada_vishama']:
                    pada_matches.append((meter_tuple, confidence, match_type))
                elif match_type in ['vedic_syllable', 'syllable_count']:
                    syllable_matches.append((meter_tuple, confidence, match_type))
                elif match_type == 'fuzzy':
                    fuzzy_matches.append((meter_tuple, confidence, match_type))

            # Build chanda list with proper priority (pada > syllable > fuzzy)
            # But DON'T add syllable matches if we have pada matches
            if pada_matches:
                for meter_tuple, conf, mtype in pada_matches:
                    meter_name = meter_tuple[0] if isinstance(meter_tuple, tuple) else meter_tuple
                    if meter_name not in confidence_map:
                        confidence_map[meter_name] = (conf, mtype)
                        if meter_tuple not in chanda:
                            chanda.append(meter_tuple)
                found = True
            elif syllable_matches:
                # Only use top 3 syllable matches to avoid flooding
                for meter_tuple, conf, mtype in syllable_matches[:3]:
                    meter_name = meter_tuple[0] if isinstance(meter_tuple, tuple) else meter_tuple
                    if meter_name not in confidence_map:
                        confidence_map[meter_name] = (conf, mtype)
                        if meter_tuple not in chanda:
                            chanda.append(meter_tuple)
                found = True
            elif fuzzy_matches:
                for meter_tuple, conf, mtype in fuzzy_matches:
                    meter_name = meter_tuple[0] if isinstance(meter_tuple, tuple) else meter_tuple
                    if meter_name not in confidence_map:
                        confidence_map[meter_name] = (conf, mtype)
                        if meter_tuple not in chanda:
                            chanda.append(meter_tuple)
                found = True

            # =====================================================================
            # VEDIC-CLASSICAL MAPPING ENRICHMENT (SIH 2025)
            # Apply empirical mappings to boost confidence for Vedic text predictions
            # E.g., If predicted "ऋषभगजविलसित" for a Vedic verse, and it matches
            # "चतुष्पदा भुरिग्जगती" → "ऋषभगजविलसित" mapping (46/47 times), boost it
            # =====================================================================
            if VEDIC_MAPPINGS_AVAILABLE and vedic_priority_meter and confidence_map:
                classical_equivalents = get_classical_equivalents(vedic_priority_meter)
                if classical_equivalents:
                    for equiv_name in classical_equivalents[:3]:  # Top 3 mappings
                        # Check if this equivalent is already in our predictions
                        for meter_name in list(confidence_map.keys()):
                            normalized_pred = normalize_vedic_meter(meter_name)
                            normalized_equiv = normalize_vedic_meter(equiv_name)

                            if normalized_pred == normalized_equiv:
                                # Boost confidence for empirically validated mapping
                                current_conf, current_type = confidence_map[meter_name]
                                if current_conf < CONFIDENCE_VEDIC_CLASSICAL_MAP:
                                    confidence_map[meter_name] = (
                                        CONFIDENCE_VEDIC_CLASSICAL_MAP,
                                        f'vedic_classical_map_{current_type}',
                                    )
            # =====================================================================

            # =====================================================================
            # FUZZY PATTERN MATCHING (INTERMEDIATE FALLBACK)
            # When exact matching fails (confidence < 5.0), try fuzzy matching
            # to catch variant patterns (e.g., Sragdhara with 1 L-G difference)
            # This runs BEFORE Vedic range fallback to preserve pattern-based matches
            # =====================================================================
            max_existing_confidence = max((conf for conf, _ in confidence_map.values()), default=0)
            has_classical_fuzzy_match = False  # Track if we found a classical meter via fuzzy

            if max_existing_confidence < 5.0 and not fuzzy:
                # Try fuzzy matching to find close pattern matches
                fuzzy_matches = self.match_with_confidence(lg_str, fuzzy=True, max_fuzzy=k)

                # List of Vedic meter names (which should use Vedic range fallback instead)
                vedic_meter_names = {
                    'गायत्री',
                    'gāyatrī',
                    'gayatri',
                    'Gāyatrī',
                    'त्रिष्टुभ्',
                    'triṣṭubh',
                    'tristubh',
                    'Triṣṭubh',
                    'जगती',
                    'jagatī',
                    'jagati',
                    'Jagatī',
                    'अनुष्टुभ्',
                    'anuṣṭubh',
                    'anustubh',
                    'Anuṣṭubh',
                    'उष्णिक्',
                    'uṣṇik',
                    'usnik',
                    'बृहती',
                    'bṛhatī',
                    'brhati',
                    'पङ्क्ति',
                    'paṅkti',
                    'pankti',
                    'प्रगाथ',
                    'pragātha',
                    'pragatha',
                    'विराट्',
                    'virāṭ',
                    'virat',
                }

                for meter_tuple, confidence, match_type in fuzzy_matches:
                    meter_name = meter_tuple[0]
                    # Only consider fuzzy matches with reasonable confidence (>3.0)
                    # and that are actual pattern matches (not syllable-count-only)
                    if confidence >= 3.0 and match_type in ['fuzzy', 'exact']:
                        if meter_name not in confidence_map or confidence > confidence_map[meter_name][0]:
                            confidence_map[meter_name] = (confidence, f'fuzzy_fallback_{match_type}')
                            if meter_tuple not in chanda:
                                chanda.append(meter_tuple)
                            found = True

                            # Track if this is a non-Vedic (classical) meter
                            if meter_name.lower() not in {m.lower() for m in vedic_meter_names}:
                                has_classical_fuzzy_match = True

                # Re-evaluate max confidence after fuzzy matching
                max_existing_confidence = max((conf for conf, _ in confidence_map.values()), default=0)

            # =====================================================================
            # VEDIC METER RANGE MATCHING (FINAL FALLBACK)
            # Only applies when NO high-confidence matches were found
            # AND we haven't found a classical meter via fuzzy matching
            # (Classical meters like Sragdhara should not be overridden by Vedic ranges)
            # Handles real-world Rigveda verses with ±1-3 syllable variance
            # E.g., Triṣṭubh peaks at 43 but has many 41-42 syllable verses
            # =====================================================================
            # Skip Vedic fallback if we found a classical meter via fuzzy matching
            # (e.g., Sragdhara variant should not be overridden by Gāyatrī range)
            needs_vedic_fallback = (
                max_existing_confidence < 5.0
                and syllable_count not in vedic_syllable_counts
                and not has_classical_fuzzy_match
            )

            if needs_vedic_fallback:
                # Priority weights for major vs rare meters (higher = more common)
                METER_FREQUENCY_WEIGHT = {
                    'त्रिष्टुभ्': 100,  # 3727 verses in Rigveda
                    'गायत्री': 100,  # 2171 verses
                    'जगती': 100,  # 1070 verses
                    'अनुष्टुभ्': 100,  # 656 verses
                    'उष्णिक्': 80,  # 448 verses
                    'बृहती': 70,  # 269 verses
                    'पङ्क्ति': 70,  # 204 verses
                    # Rare/composite meters - lower priority
                    'प्रगाथ': 50,  # Composite
                    'विराट्': 30,  # Rare
                    'ज्योतिस्': 20,  # Rare, requires refrain
                    'महापङ्क्ति': 20,  # Rare, requires refrain
                    'ककुभ्': 30,  # 3-pada structure
                    'द्विपदा त्रिष्टुभ्': 30,
                }

                # Check if syllable count falls within any Vedic meter range
                vedic_range_matches = []
                for meter_name, (low, high) in self.VEDIC_METER_RANGES.items():
                    if low <= syllable_count <= high:
                        # Skip Jyotis and Mahāpaṅkti unless there's evidence of refrain
                        if meter_name in ['ज्योतिस्', 'महापङ्क्ति']:
                            continue

                        peak = self.VEDIC_METER_PEAKS.get(meter_name, (low + high) // 2)
                        diff = abs(syllable_count - peak)
                        freq_weight = METER_FREQUENCY_WEIGHT.get(meter_name, 10)
                        # Score combines closeness to peak AND frequency weight
                        score = freq_weight - diff * 10  # 10 penalty per syllable diff
                        vedic_range_matches.append((meter_name, diff, peak, score))

                if vedic_range_matches:
                    # Sort by combined score (highest first)
                    vedic_range_matches.sort(key=lambda x: -x[3])
                    best_match = vedic_range_matches[0]
                    vedic_priority_meter = best_match[0]
                    # Confidence based on distance from peak
                    vedic_priority_confidence = max(7.0, 11.0 - best_match[1] * 0.5)

                    vedic_tuple = (vedic_priority_meter, ('',))
                    confidence_map[vedic_priority_meter] = (vedic_priority_confidence, 'vedic_range_fallback')
                    chanda.insert(0, vedic_tuple)
                    found = True
            # =====================================================================

        # Sort chanda by confidence (highest first), preserving database order for ties
        chanda_with_confidence = [
            (name, confidence_map.get(name[0] if isinstance(name, tuple) else name, (0, ''))[0], idx)
            for idx, name in enumerate(chanda)
        ]
        # Sort by confidence desc, then by original order (for ties)
        chanda_with_confidence.sort(key=lambda x: (-x[1], x[2]))
        chanda = [item[0] for item in chanda_with_confidence]

        # Store confidence information for debugging/analysis
        answer['confidence_scores'] = confidence_map

        # Determine number of padas from syllable count
        syllable_count = len(lg_str)
        if syllable_count % 4 == 0:
            num_padas_detected = 4
        elif syllable_count % 3 == 0:
            num_padas_detected = 3
        elif syllable_count % 2 == 0:
            num_padas_detected = 2
        else:
            num_padas_detected = 1

        # Generate human-readable confidence reasons
        # CRITICAL: Always use the FULL syllable count (len(lg_str)), not per-pada count
        # This ensures confidence messages show "28 syllables" not "14 syllables" for उष्णिक्
        full_syllable_count = len(lg_str)  # Total syllables in the entire input
        answer['confidence_reasons'] = build_confidence_reasons(
            confidence_scores=confidence_map,
            pattern=lg_str,
            syllable_count=full_syllable_count,  # Use FULL count, not divided
            num_padas=num_padas_detected,
        )
        answer['primary_confidence_reason'] = get_primary_confidence_reason(
            confidence_scores=confidence_map,
            pattern=lg_str,
            syllable_count=full_syllable_count,  # Use FULL count, not divided
            num_padas=num_padas_detected,
        )

        # display properties
        display_line = line
        display_syllables = direct_match['syllables']
        display_lg = full_lg
        display_gana = ' / '.join(gana).translate(self.ttable_out) if gana else full_gana
        display_length = ' / '.join(length) if length else full_length
        display_matra = ' / '.join(matra) if matra else full_matra

        # Format chanda for display, handling both tuple and string formats
        display_chanda_parts = []
        display_chanda_primary_parts = []  # High-confidence matches (exact pattern matches)
        display_chanda_alternate_parts = []  # Medium-confidence matches

        # Find maximum confidence to calculate thresholds
        max_confidence = max((conf for meter, (conf, _) in confidence_map.items()), default=0)

        # Primary threshold: 80% of max confidence (for exact matches)
        # This ensures exact matches (10.0) show as primary, but not syllable-only matches (5.0)
        confidence_threshold_primary = max_confidence * 0.8

        # Alternate threshold: Only show if confidence is at least 7.0 (higher than syllable-only)
        # This filters out the hundreds of syllable-count-only matches
        confidence_threshold_alternate = 7.0

        for c in chanda:
            if isinstance(c, (tuple, list)) and len(c) >= 2:
                formatted = self.format_chanda_pada(c[0], c[1])
                meter_name = c[0]
            elif isinstance(c, (tuple, list)) and len(c) == 1:
                formatted = self.format_chanda_pada(c[0], ('',))
                meter_name = c[0]
            else:
                formatted = str(c)
                meter_name = c

            if formatted:  # Only add non-None, non-empty strings
                meter_confidence = confidence_map.get(meter_name, (0, ''))[0]

                # Add IAST transliteration if meter name is in Devanagari
                meter_display = formatted
                if meter_name and any(ord(ch) > 127 for ch in meter_name):
                    # Transliterate to IAST
                    iast_name = transliterate(meter_name, sanscript.DEVANAGARI, sanscript.IAST)
                    # Only add if it's different (not already in IAST)
                    if iast_name and iast_name != meter_name:
                        meter_display = f"{formatted} ({iast_name})"

                # Categorize by confidence
                if meter_confidence >= confidence_threshold_primary:
                    # Primary display: high-confidence with scores (exact pattern matches)
                    formatted_with_conf = f"{meter_display} [{meter_confidence:.1f}]"
                    display_chanda_primary_parts.append(formatted_with_conf)
                elif meter_confidence >= confidence_threshold_alternate:
                    # Alternate display: medium-confidence (pada matches, vedic, etc.)
                    display_chanda_alternate_parts.append(meter_display)

                # Always add to full list (for backwards compatibility)
                display_chanda_parts.append(formatted)

        display_chanda = ' / '.join(display_chanda_parts)
        display_chanda_primary = ' | '.join(display_chanda_primary_parts)
        display_chanda_alternate = ' / '.join(display_chanda_alternate_parts)
        display_chanda_alternate_count = len(display_chanda_alternate_parts)
        display_chanda_hidden_count = (
            len(display_chanda_parts) - len(display_chanda_primary_parts) - len(display_chanda_alternate_parts)
        )

        display_jaati = ' / '.join(jaati if jaati else full_jaati)

        answer['found'] = found
        answer['syllables'] = direct_match['syllables']
        answer['lg'] = full_lg
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati

        # =====================================================================
        # PROSE DETECTION (Gadya vs Padya)
        # =====================================================================
        # Determine if the text is likely poetry (Padya) or prose (Gadya)
        # This helps users understand when input doesn't match any known meter
        # =====================================================================
        is_poetry, padya_reason, padya_confidence = self.is_padya(
            lg_str, len(lg_str), confidence_map if confidence_map else None
        )

        answer['is_padya'] = is_poetry
        answer['padya_reason'] = padya_reason
        answer['padya_confidence'] = padya_confidence

        # If not poetry and no chanda found, add a helpful message
        if not is_poetry and not found:
            answer['prose_message'] = (
                "यह पाठ गद्य (Gadya/Prose) प्रतीत होता है। "
                "गद्य में कोई निश्चित छन्द नहीं होता। "
                "(This text appears to be prose. Prose does not follow any specific meter.)"
            )
        elif not is_poetry and found:
            # Low confidence match - might be prose with accidental pattern
            answer['prose_message'] = (
                f"टिप्पणी: {padya_reason} (Note: Low confidence - text may be prose with accidental pattern match.)"
            )
        else:
            answer['prose_message'] = None
        # =====================================================================

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
        answer['display_gana'] = display_gana
        answer['display_length'] = display_length
        answer['display_matra'] = display_matra
        answer['display_chanda'] = display_chanda
        answer['display_chanda_primary'] = display_chanda_primary  # High-confidence (≥15.0)
        answer['display_chanda_alternate'] = display_chanda_alternate  # Medium-confidence (≥50% of max)
        answer['display_chanda_alternate_count'] = display_chanda_alternate_count  # Count of medium-conf matches
        answer['display_chanda_hidden_count'] = display_chanda_hidden_count  # Count of low-conf matches (<50%)
        answer['display_jaati'] = display_jaati

        answer['fuzzy'] = []

        if not found and fuzzy:
            for chanda_lg, chanda_names in self.CHANDA.items():
                chanda_gana = self.lg_to_gana(chanda_lg)
                cost, suggestion = self.transform(line, chanda_lg)
                similarity = 1 - cost / len(chanda_lg)
                # Fixed: Always add suggestions even if transformation is None (Bug #4)
                output = suggestion if suggestion else []
                _display_chanda = ' / '.join(self.format_chanda_pada(c, p) for c, p in chanda_names)
                answer['fuzzy'].append(
                    {
                        "chanda": chanda_names,
                        "gana": chanda_gana.translate(self.ttable_out),
                        "suggestion": output,
                        "cost": cost,
                        "similarity": similarity,
                        "display_chanda": _display_chanda,
                    }
                )
            answer['fuzzy'] = sorted(answer['fuzzy'], key=lambda x: x["similarity"], reverse=True)[:k]

        # =====================================================================
        # PATTERN VALIDATION INFO (for frontend display)
        # =====================================================================
        # Add expected pattern info for the primary identified meter
        # This helps users understand if their verse matches the canonical form
        # =====================================================================
        primary_meter_name = None
        if chanda:
            first_chanda = chanda[0]
            if isinstance(first_chanda, (tuple, list)) and len(first_chanda) >= 1:
                primary_meter_name = first_chanda[0]
            else:
                primary_meter_name = str(first_chanda)

        if primary_meter_name:
            meter_info = self.get_meter_info(primary_meter_name)
            pattern_validation = self.validate_pattern(lg_str, primary_meter_name)

            answer['meter_info'] = (
                {
                    'name': primary_meter_name,
                    'expected_pattern': meter_info.get('pattern') if meter_info else None,
                    'expected_syllables': meter_info.get('syllables') if meter_info else None,
                    'expected_matras': meter_info.get('matras') if meter_info else None,
                    'gana_notation': meter_info.get('gana') if meter_info else None,
                    'meter_type': meter_info.get('type') if meter_info else None,
                    'yati': meter_info.get('yati') if meter_info else None,
                    'padas': meter_info.get('padas') if meter_info else None,
                }
                if meter_info
                else None
            )

            answer['pattern_validation'] = {
                'is_valid': pattern_validation.get('is_valid'),
                'expected_pattern': pattern_validation.get('expected_pattern'),
                'actual_pattern': pattern_validation.get('actual_pattern'),
                'match_percentage': pattern_validation.get('match_percentage'),
                'mismatches': pattern_validation.get('mismatches'),
            }
        else:
            answer['meter_info'] = None
            answer['pattern_validation'] = None
        # =====================================================================

        return answer

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
            from sandhi_rules import gen_candidates
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
