"""Laghu/guru pattern matching against the meter definitions, with confidence scores.

Mixed into backend.core.chanda.Chanda; methods rely on its other mixins through self.
"""

import Levenshtein as Lev
import sanskrit_text as skt

from .chanda_constants import (
    PATTERN_MISMATCH_MAX,
)
from .chanda_validation import PatternValidationMixin


class PatternMatchMixin(PatternValidationMixin):
    def match_with_confidence(self, lg_pattern, fuzzy=False, max_fuzzy=10):
        """
        Multi-level matching with confidence scoring

        IMPROVED: More conservative pada-level matching - requires pattern similarity,
        not just syllable count. This prevents false positives like matching
        any 16-syllable pattern to anuṣṭubh.

        CONFIDENCE SCORING SYSTEM (0.0 - 10.0 scale):
        ================================================
        Level 1: Exact Matches (Highest Priority)
        - 10.0: Exact L-G pattern match (CONFIDENCE_EXACT_PATTERN)
        - 9.0:  Regex pattern match with wildcards (CONFIDENCE_EXACT_REGEX)

        Level 2: Structural Matches (High Priority)
        - 9.0:  Exact pada-level sama pattern (CONFIDENCE_PADA_EXACT)
        - 8.0:  Vedic meter with sama pada structure (CONFIDENCE_PADA_VEDIC_SAMA)
        - 7.5:  Similar pada-level pattern (CONFIDENCE_PADA_SIMILAR)
        - 6.5:  Vedic meter with similar pada structure (CONFIDENCE_PADA_VEDIC_SIMILAR)

        Level 3: Syllable Count Matches (Medium Priority)
        - 6.0:  Vedic meter by syllable count (CONFIDENCE_VEDIC_SYLLABLE)
        - 4.0:  Generic syllable count match (CONFIDENCE_SYLLABLE_COUNT)

        Level 4: Fuzzy Matches (Low Priority - optional)
        - 1.0-4.0: Levenshtein distance-based match (CONFIDENCE_FUZZY_MIN to CONFIDENCE_FUZZY_MAX)

        Args:
            lg_pattern (str): L-G pattern to match
            fuzzy (bool): Enable fuzzy matching (default: False)
            max_fuzzy (int): Maximum fuzzy results to return (default: 10)

        Returns:
            List of tuples: [(meter_names, confidence_score, match_type), ...]
            Sorted by confidence (descending)
        """
        results = []
        syllable_count = len(lg_pattern)

        # Level 1: Exact match (highest confidence)
        if lg_pattern in self.CHANDA:
            for meter_name in self.CHANDA[lg_pattern]:
                results.append((meter_name, 10.0, 'exact'))

        # Level 2: Pada-level matching - IMPROVED with pattern verification
        # Only match if padas are structurally similar (sama) or follow known vishama pattern
        # Don't just match based on syllable count - that causes too many false positives

        # Skip pada matching if we already have exact matches
        if not results:
            for num_padas in [4, 3, 2]:
                padas = self.split_into_padas(lg_pattern, num_padas)
                if padas:
                    first_pada = padas[0]
                    pada_syllables = len(first_pada)

                    # Check if all padas are identical (sama pattern)
                    all_sama = all(pada == first_pada for pada in padas)

                    # Check if padas are similar (allow 1-2 differences per pada)
                    # This is more lenient than exact sama but still structural
                    similar_padas = all(Lev.distance(pada, first_pada) <= PATTERN_MISMATCH_MAX for pada in padas)

                    # Only proceed with pada matching if we have structural similarity
                    if all_sama or similar_padas:
                        # Try to find this pada pattern in our database
                        if first_pada in self.SINGLE_CHANDA:
                            # Great! We found the exact pada pattern
                            for meter_name in self.SINGLE_CHANDA[first_pada]:
                                if all_sama:
                                    results.append((meter_name, 9.0, 'pada_exact_sama'))
                                else:
                                    results.append((meter_name, 7.5, 'pada_similar'))

                        # Also check for Vedic meters by pada structure
                        vedic_pada_meters = {
                            8: ('अनुष्टुभ्', 32),  # Anushtubh: 4×8
                            11: ('त्रिष्टुभ्', 44),  # Trishtubh: 4×11
                            12: ('जगती', 48),  # Jagati: 4×12
                        }

                        if pada_syllables in vedic_pada_meters:
                            meter_name, expected_total = vedic_pada_meters[pada_syllables]
                            # Only match if total syllables are close to expected
                            if abs(syllable_count - expected_total) <= 4:
                                if all_sama:
                                    results.append(((meter_name, ('',)), 8.0, 'pada_vedic_sama'))
                                elif similar_padas:
                                    results.append(((meter_name, ('',)), 6.5, 'pada_vedic_similar'))

        # Level 3: Syllable count matching - ONLY if no pada matches found
        # This is low-confidence fallback
        if not results:
            vedic_meter, vedic_info = self.identify_vedic_meter(syllable_count, lg_pattern)
            if vedic_meter:
                results.append(((vedic_meter, ('',)), 6.0, 'vedic_syllable'))

            # Don't flood with syllable_count matches - they're too unreliable
            # Only add if no other matches and pattern is short (likely single pada)
            if not results and syllable_count <= 16:
                syllable_matches = self.find_by_syllable_count(syllable_count)
                for match in syllable_matches[:3]:  # Limit to top 3
                    results.append((match, 4.0, 'syllable_count'))

        # Level 4: Fuzzy matching (lowest confidence, only if enabled and no results)
        if fuzzy and not results:
            for chanda_lg, chanda_names in self.CHANDA.items():
                if len(chanda_lg) == syllable_count:
                    distance = Lev.distance(lg_pattern, chanda_lg)
                    if distance <= 3:
                        similarity = 1 - (distance / len(chanda_lg))
                        confidence = similarity * 4.0

                        for name in chanda_names:
                            if name not in [r[0] for r in results]:
                                results.append((name, confidence, 'fuzzy'))

        # Sort by confidence (descending)
        results.sort(key=lambda x: x[1], reverse=True)

        return results

    def find_by_syllable_count(self, syllable_count):
        """Find chandas by syllable count as fallback"""
        matches = []

        # Search in existing CHANDA database for matching syllable counts
        for lg_pattern, chanda_names in self.CHANDA.items():
            if len(lg_pattern) == syllable_count:
                matches.extend(chanda_names)

        # If no exact matches, check if it's a recognized Vedic meter total
        if not matches:
            meter_name, meter_info = self.identify_vedic_meter(syllable_count)
            if meter_name and meter_info:
                # Create a pseudo-entry for the Vedic meter
                matches.append((meter_name, ('1',)))

        return matches

    ###########################################################################

    def transform(self, source_line, signature, replace_cost=1, delete_cost=1, insert_cost=1, max_diff=3):
        """
        Find possible transformations of source string to fit the signature

        Note: LRU cache removed - returns unhashable types (nested lists).
        This method is called during fuzzy matching which is opt-in,
        so performance impact is acceptable.
        """
        syllables, lg_marks = self.mark_lg(source_line)
        # Note: Can avoid this conversion to save time, if needed
        # Just need to ensure that Laghu-Guru string is passed properly
        lg_signature = self.gana_to_lg(signature)
        lg_str = ''.join(lg_marks)
        ops = Lev.editops(lg_str, lg_signature)

        if not ops:
            # exact match
            return 0, []

        distance = len(ops)

        # weights can be decided by an external agent
        op_cost = {'replace': replace_cost, 'delete': delete_cost, 'insert': insert_cost}

        cost = sum([op_cost[op[0]] for op in ops])

        if distance > max_diff:
            return distance, None

        idx = 0  # overall index (syllables, lg_marks)
        lg_idx = 0  # index in the lg_str
        op_idx = 0  # index in the list of edit operations

        output = []

        op, spos, dpos = ops[op_idx]

        # ------------------------------------------------------------------- #
        for _lid, line in enumerate(syllables):
            output_line = []
            # --------------------------------------------------------------- #
            for _wid, word in enumerate(line):
                output_word = []
                # ----------------------------------------------------------- #
                for _cid, syllable in enumerate(word):
                    output_syllable = syllable
                    if lg_marks[idx]:
                        if lg_idx == spos:
                            if op[0] == 'i':
                                output_syllable = f'i({lg_signature[dpos]})'
                                output_word.append(output_syllable)
                                op_idx += 1
                                # insertion means we need to continue with
                                # the same syllable but next operation,
                                # so we increment op_idx
                                # Hence the other condition (op[0] != 'i')
                                # cannot be in the 'else' part directly

                            if op_idx < distance:
                                op, spos, dpos = ops[op_idx]

                                if op[0] != 'i':
                                    output_syllable = f'{op[0]}({syllable})'
                                    if op[0] == 'r':
                                        substitute = lg_signature[dpos]
                                        output_syllable += f'[{substitute}]'
                                        laghu = skt.is_laghu(syllable)
                                        if not laghu == (substitute == self.L):
                                            tm = skt.toggle_matra(syllable)
                                            if tm:
                                                # toggle was successful
                                                output_syllable += f'{{{tm}}}'
                                op_idx += 1
                                if op_idx < distance:
                                    op, spos, dpos = ops[op_idx]

                        # increase index in Laghu-Guru string if valid mark
                        lg_idx += 1

                    # always increment syllable index
                    idx += 1
                    output_word.append(output_syllable)
                # ----------------------------------------------------------- #
                output_line.append(output_word)
            # --------------------------------------------------------------- #
            output.append(output_line)
        # ------------------------------------------------------------------- #

        return cost, output

    ###########################################################################

    def find_direct_match(self, line, multi=False):
        chanda_dictionary = self.MULTI_CHANDA if multi else self.SINGLE_CHANDA

        syllables, lg_marks = self.mark_lg(skt.clean(line))
        flat_syllables = [s for ln in syllables for w in ln for s in w]
        lg_str = ''.join(lg_marks)
        if not lg_str:
            return None

        found = lg_str in chanda_dictionary

        # try searching by making last Guru using Anta-guru principle (Bug #5)
        if not found and lg_str[-1] == self.L:
            if self.should_be_guru(flat_syllables[-1], is_last=True):
                lg_str = lg_str[:-1] + self.G
                found = lg_str in chanda_dictionary

                # still not found? revert
                if not found:
                    lg_str = lg_str[:-1] + self.L

        # Method 2: Syllable count fallback (Bug #3)
        syllable_count_matches = []
        if not found:
            syllable_count = len(lg_str)
            syllable_count_matches = self.find_by_syllable_count(syllable_count)
            if syllable_count_matches:
                found = True

        chanda = []
        jaati = []
        gana = []
        length = []
        matra = []
        if not multi:
            if found:
                if lg_str in self.SINGLE_CHANDA:
                    chanda += self.SINGLE_CHANDA.get(lg_str)
                # Add syllable count matches
                if syllable_count_matches:
                    chanda += syllable_count_matches
            jaati = self.JAATI.get(len(lg_str), self.JAATI[-1])
            gana = [self.lg_to_gana(lg_str)]
            length = [str(len(lg_str))]
            matra = [str(self.count_matra(lg_str))]
        else:
            if found:
                chanda = self.MULTI_CHANDA.get(lg_str, [])
                # display properties, bit misplaced
                splits_data = self.SPLITS.get(lg_str, [])
                if splits_data:
                    jaati = [
                        "("
                        + ', '.join(' / '.join(self.JAATI.get(len(split), self.JAATI[-1])) for split in splits)
                        + ")"
                        for splits in splits_data
                    ]
                    gana = [f"({', '.join(self.lg_to_gana(s) for s in splits)})" for splits in splits_data]
                    length = [f"({' + '.join(str(len(s)) for s in splits)})" for splits in splits_data]
                    matra = [f"({' + '.join(str(self.count_matra(s)) for s in splits)})" for splits in splits_data]
                else:
                    jaati = []
                    gana = []
                    length = []
                    matra = []

        # Track which matches are exact vs fallback
        exact_chanda = []
        if lg_str in chanda_dictionary:
            exact_chanda = chanda_dictionary.get(lg_str, [])

        match = {
            'found': found,
            'syllables': flat_syllables,
            'lg': lg_marks,
            'gana': gana,
            'chanda': chanda,
            'exact_chanda': exact_chanda,  # Only truly exact matches
            'is_fallback': bool(syllable_count_matches and not exact_chanda),
            'jaati': jaati,
            'length': length,
            'matra': matra,
        }
        return match
