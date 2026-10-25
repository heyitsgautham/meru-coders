"""Single-line meter identification: Chanda.identify_line.

Mixed into backend.core.chanda.Chanda.
"""

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate

from .chanda_constants import (
    CONFIDENCE_VEDIC_CLASSICAL_MAP,
    VEDIC_MAPPINGS_AVAILABLE,
    get_classical_equivalents,
    normalize_vedic_meter,
)
from .confidence_reasons import build_confidence_reasons, get_primary_confidence_reason


class LineIdentificationMixin:
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
