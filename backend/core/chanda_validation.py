"""Checking a line's laghu-guru pattern against one meter's expected pattern, pada by pada.

Mixed into backend.core.chanda.Chanda; identify_line reports validate_pattern's verdict for the top meter."""

from .chanda_constants import PATTERN_MATCH_TOLERANCE


class PatternValidationMixin:
    def pattern_matches_with_tolerance(self, pattern1, pattern2, tolerance=2):
        """Check if two L-G patterns match within tolerance"""
        if len(pattern1) != len(pattern2):
            return False

        differences = sum(1 for a, b in zip(pattern1, pattern2, strict=False) if a != b)
        return differences <= tolerance

    def should_be_guru(self, syllable, is_last=False):
        """Apply Anta-guru rule: last syllable is typically Guru"""
        if is_last:
            return True
        return False

    def validate_pattern(self, actual_lg, meter_name):
        """
        Validate if actual L-G pattern matches expected pattern for a meter.

        Handles:
        - Single pada patterns (8 syllables for Anuṣṭubh)
        - Multi-pada patterns (16, 32 syllables)
        - Wildcard patterns (- means any syllable)
        - Pada-specific patterns for vishama meters

        Args:
            actual_lg: Actual L-G pattern from the verse
            meter_name: Name of the identified meter

        Returns:
            Dictionary with validation results:
            {
                'is_valid': True/False,
                'expected_pattern': expected L-G pattern,
                'actual_pattern': actual L-G pattern,
                'match_percentage': 0-100,
                'mismatches': [(position, expected, actual), ...]
            }
        """
        meter_info = self.get_meter_info(meter_name)

        if not meter_info:
            return {
                'is_valid': None,  # Unknown meter
                'expected_pattern': None,
                'actual_pattern': actual_lg,
                'match_percentage': None,
                'mismatches': [],
            }

        # Get base pattern
        base_pattern = meter_info.get('pattern', '').replace('ल', self.L).replace('ग', self.G)
        expected_syllables = meter_info.get('syllables', len(base_pattern))

        # Check if base pattern has wildcards (- means any syllable)
        # If it has wildcards, prefer it over pada-specific patterns
        has_wildcards = '-' in base_pattern

        # Handle multi-pada verses
        # If actual is longer than expected, it's multiple padas
        actual_len = len(actual_lg)
        if actual_len > expected_syllables and expected_syllables > 0:
            # Calculate how many padas this could represent
            # Allow for ±1-2 syllables tolerance for Vedic meters
            num_padas_exact = actual_len // expected_syllables
            remainder = actual_len % expected_syllables

            # Check for exact match OR near-match (within 1-2 syllables of n*expected)
            is_near_match = False
            num_padas = num_padas_exact

            if remainder == 0 and num_padas <= 4:
                # Exact match
                is_near_match = True
            elif num_padas_exact >= 2 and num_padas_exact <= 4:
                # Check if we're close to an exact multiple
                expected_total = num_padas_exact * expected_syllables
                next_expected_total = (num_padas_exact + 1) * expected_syllables

                # Allow ±2 syllables tolerance
                if abs(actual_len - expected_total) <= 2:
                    is_near_match = True
                    num_padas = num_padas_exact
                elif abs(actual_len - next_expected_total) <= 2 and (num_padas_exact + 1) <= 4:
                    is_near_match = True
                    num_padas = num_padas_exact + 1

            if is_near_match and num_padas <= 4:
                # Repeat pattern for multiple padas
                padas_info = meter_info.get('padas', {})

                # Use base pattern if it has wildcards (more flexible)
                # Otherwise, try pada-specific patterns
                if has_wildcards:
                    # Repeat wildcard pattern
                    expected = base_pattern * num_padas
                elif padas_info and len(padas_info) >= num_padas:
                    # Use pada-specific patterns
                    expected_parts = []
                    for i in range(1, num_padas + 1):
                        pada_key = str(i)
                        if pada_key in padas_info:
                            pada_pattern = padas_info[pada_key].get('pattern', base_pattern)
                            pada_pattern = pada_pattern.replace('ल', self.L).replace('ग', self.G)
                            expected_parts.append(pada_pattern)
                        else:
                            expected_parts.append(base_pattern)
                    expected = ''.join(expected_parts)
                else:
                    # Repeat base pattern
                    expected = base_pattern * num_padas
            else:
                expected = base_pattern
        else:
            expected = base_pattern

        # Handle wildcard patterns (- means any, translates to [LG])
        if '-' in expected:
            # Convert to regex pattern
            regex_pattern = expected.replace('-', '[LG]')
            try:
                import re

                pattern_re = re.compile(f'^{regex_pattern}$', re.IGNORECASE)
                is_match = bool(pattern_re.match(actual_lg))

                # Count fixed positions that match
                fixed_count = 0
                fixed_total = 0
                for i, c in enumerate(expected):
                    if c != '-' and i < len(actual_lg):
                        fixed_total += 1
                        if c.upper() == actual_lg[i].upper():
                            fixed_count += 1

                # Match percentage based on fixed positions
                match_pct = (fixed_count / fixed_total * 100) if fixed_total > 0 else 100

                return {
                    'is_valid': is_match,
                    'expected_pattern': expected,
                    'actual_pattern': actual_lg,
                    'match_percentage': round(match_pct, 1),
                    'mismatches': [] if is_match else [('pattern_mismatch', expected, actual_lg)],
                }
            except Exception:
                pass

        # Handle regex patterns (already contains [])
        if '[' in expected or '?' in expected or '*' in expected:
            try:
                import re

                pattern_re = re.compile(f'^{expected}$', re.IGNORECASE)
                is_match = bool(pattern_re.match(actual_lg))
                return {
                    'is_valid': is_match,
                    'expected_pattern': expected,
                    'actual_pattern': actual_lg,
                    'match_percentage': 100 if is_match else 0,
                    'mismatches': [] if is_match else [('pattern', expected, actual_lg)],
                }
            except Exception:
                pass

        # Direct comparison
        mismatches = []
        match_count = 0

        # Compare character by character
        min_len = min(len(expected), len(actual_lg))
        for i in range(min_len):
            if expected[i].upper() == actual_lg[i].upper():
                match_count += 1
            else:
                mismatches.append((i + 1, expected[i], actual_lg[i]))

        # Account for length difference
        if len(expected) != len(actual_lg):
            mismatches.append(('length', len(expected), len(actual_lg)))

        max_len = max(len(expected), len(actual_lg), 1)
        match_pct = (match_count / max_len) * 100

        return {
            'is_valid': match_pct >= PATTERN_MATCH_TOLERANCE,  # Allow 10% tolerance
            'expected_pattern': expected,
            'actual_pattern': actual_lg,
            'match_percentage': round(match_pct, 1),
            'mismatches': mismatches,
        }
