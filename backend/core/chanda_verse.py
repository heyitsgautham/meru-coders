"""Verse-level scoring for Chanda.identify_from_text.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
identify_from_text identifies every line, then calls these in order: score each
four-line verse, let Vedic mode override the result when the text is Vedic,
name the mode that won, and optionally write the result files.
"""

import hashlib
import json
import os
from collections import Counter

from .chanda_constants import (
    CONFIDENCE_VEDIC_CLASSICAL_MAP,
    VEDIC_MAPPINGS_AVAILABLE,
    get_classical_equivalents,
    normalize_vedic_meter,
)


class VerseScoringMixin:
    def _score_verses(self, line_results, verse_aggregates, scheme):
        """Combine the line results of each four-line verse into a verse-level meter ranking."""
        verse_results = []
        # The holistic result of the last verse, as the pre-aggregation loop leaves it.
        holistic_result = verse_aggregates[-1]['holistic'] if verse_aggregates else None
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
                    self._boost_holistic_meter(holistic_result, line_results, verse_aggregate_idx, ongoing_score)

                holistic_boost_applied = True

            if _result['found']:
                _chanda = _result['chanda']
                _unique_chanda = list(dict(_chanda))

                # ENHANCED: Use confidence scores from multi-level matching
                confidence_scores = _result.get('confidence_scores', {})

                self._apply_vedic_classical_map(holistic_result, confidence_scores)

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
                best_matches = self._rank_verse_meters(verse_scores)
                verse_result['scores'] = verse_scores
                verse_result['chanda'] = best_matches
                verse_aggregate_idx += 1
                holistic_boost_applied = False  # Reset for next verse
                for _line_idx in verse_result['lines']:
                    self._prioritise_matching_fuzzy(line_results[_line_idx], best_matches)

                verse_results.append(verse_result)
                # reset
                verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}
                ongoing_score = Counter()
        return verse_results

    def _apply_vedic_mode(self, text, mode, verse, line_results, verse_results, scheme):
        """Replace the verse results with Vedic mode's syllable-count meter when the text is Vedic.

        Returns the verse results to use; line_results gain the Vedic meter in place when it wins.
        """
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
        return verse_results

    @staticmethod
    def _effective_mode_used(mode, verse_results):
        """'vedic' or 'classical' for auto mode, from the winning verse meter; otherwise the requested mode."""
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
        return effective_mode_used

    def _save_results(self, text, verse, fuzzy, results, save_path):
        """Write the result as JSON and plain text under save_path; return the file names, or None for each."""
        line_results = results['line']
        verse_results = results['verse']
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

        return {'json': json_filename, 'txt': txt_filename}

    def _boost_holistic_meter(self, holistic_result, line_results, verse_aggregate_idx, ongoing_score):
        """Add the holistic Vedic meter's boost to ongoing_score at the start of a verse.

        A structure-confirmed Vedic meter (4×11, 4×12 and so on) gets +8 and pada-level meters
        drop to 30%, unless a classical meter matches exactly in most lines; an unconfirmed
        verse of three or more lines gets +2.
        """
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

    @staticmethod
    def _apply_vedic_classical_map(holistic_result, confidence_scores):
        """Raise classical meters that empirically map to the verse's Vedic meter to the mapping confidence."""
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

    @staticmethod
    def _rank_verse_meters(verse_scores):
        """(tied best meters, score), classical meters ahead of the generic Vedic categories on a tie."""
        if verse_scores:
            best_score = verse_scores[0][1]
            tied_meters = [_c for _c, _score in verse_scores if _score == best_score]

            # Tiebreaker: prefer specific classical meters over generic Vedic ones
            # Vedic category meters (generic): त्रिष्टुभ्, जगती, गायत्री, अनुष्टुभ्, etc.
            vedic_category_meters = {'त्रिष्टुभ्', 'जगती', 'गायत्री', 'अनुष्टुभ्', 'उष्णिक्', 'बृहती', 'पङ्क्ति'}

            # Sort: classical meters first, then Vedic category meters
            def meter_priority(m):
                # 0 = classical (preferred), 1 = Vedic category
                return 1 if m in vedic_category_meters else 0

            tied_meters.sort(key=meter_priority)
            best_matches = (tied_meters, best_score)
        else:
            best_matches = ([], 0)
        return best_matches

    @staticmethod
    def _prioritise_matching_fuzzy(line_result, best_matches):
        """Move fuzzy matches that name a winning verse meter to the front of the line's fuzzy list."""
        priority_fuzzy = []
        existing_fuzzy = line_result['result']['fuzzy']
        for idx, fuzzy_match in enumerate(existing_fuzzy):
            if any([(x in best_matches[0]) for x in [c[0] for c in fuzzy_match['chanda']]]):
                priority_fuzzy.append(existing_fuzzy.pop(idx))
        line_result['result']['fuzzy'] = priority_fuzzy + existing_fuzzy
