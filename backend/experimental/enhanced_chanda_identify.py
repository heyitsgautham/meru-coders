"""Line and text identification for EnhancedChanda.

Mixed into backend.experimental.enhanced_chanda.EnhancedChanda; methods rely on its tables and matching mixins through self."""

import re
from collections import Counter

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate


class EnhancedIdentifyMixin:
    def identify_line(self, line, fuzzy=False, k=10):
        """Identify Chanda from a single line"""
        lines, scheme = self.process_text(line)
        output_scheme = scheme if scheme != sanscript.DEVANAGARI else None

        if len(lines) > 1:
            # Concatenate multi-line input
            line = ' '.join(lines)
        elif len(lines) == 1:
            line = lines[0]
        else:
            return {}

        answer = {}

        direct_match = self.find_direct_match(line)
        multi_match = self.find_direct_match(line, multi=True)

        if direct_match is None:
            return answer

        found = direct_match['found'] or multi_match['found']
        lg_str = ''.join(direct_match['lg'])

        # Regex matches
        regex_matches = [k for k in self.CHANDA if re.match(f'^{k}$', lg_str)]
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
                chanda.extend(direct_match['chanda'])
                jaati = direct_match['jaati']
                gana = direct_match['gana']
                length = direct_match['length']
                matra = direct_match['matra']
            if multi_match['found']:
                chanda.extend(multi_match['chanda'])
                if not jaati:
                    jaati = multi_match['jaati']
                length = multi_match.get('length', length)
                matra = multi_match.get('matra', matra)

            if is_regex_match:
                chanda += [c for m in regex_matches for c in self.CHANDA.get(m, []) if c not in chanda]

        full_lg = [self.output_map.get(c, c) for c in direct_match['lg']]
        full_length = len(lg_str)
        full_matra = self.count_matra(lg_str)
        full_gana = self.lg_to_gana(lg_str).translate(self.ttable_out)
        full_jaati = self.JAATI.get(len(lg_str), self.JAATI.get(-1, []))

        # ENHANCED: Multi-level matching with confidence scores
        multi_level_matches = self.match_with_confidence(lg_str, fuzzy=fuzzy, max_fuzzy=k)

        # Build confidence map
        confidence_map = {}

        # Add existing exact matches
        for c in chanda:
            meter_name = c[0] if isinstance(c, tuple) else c
            confidence_map[meter_name] = (10.0, 'exact_direct')

        # Add multi-level matches
        for match_item, confidence, match_type in multi_level_matches:
            if isinstance(match_item, tuple):
                meter_name = match_item[0]
                meter_tuple = match_item
            else:
                meter_name = match_item
                meter_tuple = (match_item, ('',))

            # Don't let Vedic family names override specific meters
            if meter_name in self.VEDIC_FAMILY_NAMES:
                if any(m not in self.VEDIC_FAMILY_NAMES for m in confidence_map.keys()):
                    # We have specific meters, skip Vedic family
                    confidence = min(confidence, 3.0)

            if meter_name in confidence_map:
                existing_conf, existing_type = confidence_map[meter_name]
                if confidence > existing_conf:
                    confidence_map[meter_name] = (confidence, match_type)
            else:
                confidence_map[meter_name] = (confidence, match_type)
                if meter_tuple not in chanda:
                    chanda.append(meter_tuple)

        # Sort chanda by confidence
        chanda_with_confidence = [
            (name, confidence_map.get(name[0] if isinstance(name, tuple) else name, (0, ''))[0]) for name in chanda
        ]
        chanda_with_confidence.sort(key=lambda x: x[1], reverse=True)
        chanda = [item[0] for item in chanda_with_confidence]

        if chanda:
            found = True

        # Classify verse type
        verse_type = self.classify_verse_type(lg_str)

        # Display properties
        display_line = line
        display_syllables = direct_match['syllables']
        display_lg = full_lg
        display_gana = ' / '.join(gana).translate(self.ttable_out) if gana else full_gana
        display_length = ' / '.join(length) if length else str(full_length)
        display_matra = ' / '.join(matra) if matra else str(full_matra)
        display_chanda = ' / '.join((c[0] if isinstance(c, tuple) else str(c)) for c in chanda[:5]) if chanda else ''
        display_jaati = ' / '.join(jaati if jaati else full_jaati)

        answer['found'] = found
        answer['syllables'] = direct_match['syllables']
        answer['lg'] = ''.join(full_lg)
        answer['gana'] = full_gana
        answer['length'] = full_length
        answer['matra'] = full_matra
        answer['chanda'] = chanda
        answer['jaati'] = jaati if jaati else full_jaati
        answer['confidence_scores'] = confidence_map
        answer['verse_type'] = verse_type

        answer['display_scheme'] = output_scheme
        answer['display_line'] = display_line
        answer['display_syllables'] = display_syllables
        answer['display_lg'] = display_lg
        answer['display_gana'] = display_gana
        answer['display_length'] = display_length
        answer['display_matra'] = display_matra
        answer['display_chanda'] = display_chanda
        answer['display_jaati'] = display_jaati

        answer['fuzzy'] = []

        # Add fuzzy results if not found
        if not found and fuzzy:
            fuzzy_results = self._fuzzy_match(lg_str, k)
            for name, conf, match_type in fuzzy_results:
                answer['fuzzy'].append({'name': name, 'confidence': conf, 'match_type': match_type})

        # Build results list for API compatibility
        answer['results'] = []
        for c in chanda[:k]:
            meter_name = c[0] if isinstance(c, tuple) else c
            conf, match_type = confidence_map.get(meter_name, (0, 'unknown'))
            answer['results'].append({'name': meter_name, 'confidence': conf, 'match_type': match_type})

        return answer

    def identify_from_text(self, text, verse=False, fuzzy=False, save_path=None, scheme=None):
        """Identify meters from text"""
        line_results = []
        verse_results = []

        lines, _scheme = self.process_text(text)
        if not scheme:
            scheme = _scheme

        for line in lines:
            if not line:
                continue
            original_line = transliterate(line, sanscript.DEVANAGARI, scheme)
            line_results.append({'line': line, 'result': self.identify_line(original_line, fuzzy=fuzzy)})

        if verse:
            verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}

            line_count = 0
            ongoing_score = Counter()

            for _line_idx, line_result in enumerate(line_results):
                line_count += 1
                result = line_result['result']

                if result.get('chanda'):
                    for c in result['chanda'][:3]:
                        name = c[0] if isinstance(c, tuple) else c
                        ongoing_score[name] += 1

                verse_result['lines'].append(line_result)

                if line_count == 4:
                    if ongoing_score:
                        best_chanda = ongoing_score.most_common(1)[0]
                        verse_result['chanda'] = best_chanda
                        verse_result['scores'] = ongoing_score.most_common()
                    verse_results.append(verse_result)

                    verse_result = {'chanda': None, 'scheme': scheme, 'scores': [], 'lines': []}
                    line_count = 0
                    ongoing_score = Counter()

            # Handle remaining lines
            if verse_result['lines']:
                if ongoing_score:
                    best_chanda = ongoing_score.most_common(1)[0]
                    verse_result['chanda'] = best_chanda
                    verse_result['scores'] = ongoing_score.most_common()
                verse_results.append(verse_result)

        results = {'line': line_results, 'verse': verse_results}

        return {
            'result': results,
            'results': line_results,  # For API compatibility
        }

    @staticmethod
    def format_chanda_pada(chanda: str, pada: tuple) -> str:
        if not chanda:
            return ''
        if isinstance(pada, tuple) and len(pada) == 1 and pada[0] == '':
            return chanda
        elif isinstance(pada, tuple) and len(pada) > 1:
            return f"{chanda} ({', '.join(str(p) for p in pada)})"
        elif pada and str(pada) != '':
            return f"{chanda} ({pada})"
        return chanda
