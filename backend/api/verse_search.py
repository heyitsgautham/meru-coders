"""Fuzzy verse search over the source corpora, and the cache lookup that lets
identify_text skip the AI validator for known verses."""

import csv
import logging

from flask import Blueprint, jsonify, request

from backend.api.datasets import load_dataset_catalog
from backend.api.helpers import SOURCE_DIR
from backend.api.text_matching import calculate_similarity, normalize_sanskrit_text
from backend.api.validation import text_payload
from backend.config import settings

logger = logging.getLogger(__name__)

bp = Blueprint('verse_search', __name__)


# Cache for sloka search index (loaded on first request)
_sloka_search_cache = {
    'initialized': False,
    'slokas': [],  # List of (sloka_text, dataset_id, chandas, row_data)
    'normalized_map': {},  # normalized_text -> original indices
}


def build_sloka_search_index():
    """
    Build search index from all datasets containing slokas.
    Called once on first search request.
    """
    if _sloka_search_cache['initialized']:
        return

    logger.info("Building sloka search index...")
    catalog = load_dataset_catalog()
    slokas = []

    for ds_id, ds_data in catalog.get('datasets', {}).items():
        sloka_col = ds_data.get('slokaColumn')
        chandas_col = ds_data.get('chandasColumn')

        if not sloka_col:
            continue  # Skip datasets without slokas

        # Handle merged datasets
        if 'files' in ds_data:
            continue  # Skip merged datasets (they contain meter definitions, not verses)

        filename = ds_data.get('filename', '')
        filepath = SOURCE_DIR / filename

        if not filepath.exists():
            continue

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row_idx, row in enumerate(reader):
                    sloka_text = row.get(sloka_col, '').strip()
                    if sloka_text:
                        chandas = row.get(chandas_col, '') if chandas_col else ''
                        slokas.append(
                            {
                                'text': sloka_text,
                                'normalized': normalize_sanskrit_text(sloka_text),
                                'dataset_id': ds_id,
                                'dataset_name': ds_data.get('name', ds_id),
                                'chandas': chandas.strip(),
                                'source': ds_data.get('source', ''),
                                'row_index': row_idx,
                                'raw': row,
                            }
                        )
        except Exception as e:
            logger.warning(f"Error loading dataset {ds_id} for search index: {e}")

    _sloka_search_cache['slokas'] = slokas
    _sloka_search_cache['initialized'] = True
    logger.info(f"Sloka search index built with {len(slokas)} entries")


# Configurable thresholds for cache-based AI skipping
CACHE_EXACT_MATCH_THRESHOLD = 0.98  # Skip AI + use cached meter directly


CACHE_CLOSE_MATCH_THRESHOLD = 0.90  # Skip AI, but still run rule engine


def find_cached_verse_match(text, threshold=CACHE_CLOSE_MATCH_THRESHOLD):
    """
    Search the verse cache for an exact or close match.
    If found, we can skip AI validation and potentially use cached meter info.

    Args:
        text: Input Sanskrit text
        threshold: Minimum similarity score to consider a match (default 0.90)

    Returns:
        dict with:
            - found: bool
            - similarity: float (0-1)
            - cached_data: dict with meter info if found
            - skip_ai: bool (whether to skip AI validation)
            - use_cached_meter: bool (whether cached meter can be used directly)
    """
    # Build index if not already done
    build_sloka_search_index()

    if not _sloka_search_cache['slokas']:
        return {'found': False, 'similarity': 0.0, 'skip_ai': False, 'use_cached_meter': False}

    # Normalize input for comparison
    normalized_input = normalize_sanskrit_text(text)

    if not normalized_input:
        return {'found': False, 'similarity': 0.0, 'skip_ai': False, 'use_cached_meter': False}

    best_match = None
    best_similarity = 0.0

    # Search through cached verses
    for sloka_data in _sloka_search_cache['slokas']:
        similarity = calculate_similarity(normalized_input, sloka_data['normalized'])

        if similarity > best_similarity:
            best_similarity = similarity
            best_match = sloka_data

            # Early exit for exact match (optimization)
            if similarity >= CACHE_EXACT_MATCH_THRESHOLD:
                break

    if best_match and best_similarity >= threshold:
        return {
            'found': True,
            'similarity': best_similarity,
            'cached_data': {
                'text': best_match['text'],
                'chandas': best_match.get('chandas', ''),
                'lg_pattern': best_match.get('raw', {}).get('lg_pattern', ''),
                'syllable_count': best_match.get('raw', {}).get('syllable_count', ''),
                'dataset': best_match.get('dataset_name', ''),
                'source': best_match.get('source', ''),
            },
            'skip_ai': True,  # Skip AI validation for close matches
            'use_cached_meter': best_similarity >= CACHE_EXACT_MATCH_THRESHOLD,
        }

    return {'found': False, 'similarity': best_similarity, 'skip_ai': False, 'use_cached_meter': False}


@bp.route(f'{settings.API_PREFIX}/sloka/search', methods=['POST'])
def search_sloka():
    """
    Search for a sloka in the datasets to find matches and identify errors.

    Request JSON:
        {
            "text": "Sloka text to search for",
            "threshold": 0.7,  // Minimum similarity (0-1), default 0.7
            "limit": 10        // Max results, default 10
        }

    Returns:
        JSON with matching slokas sorted by similarity
    """
    text_payload()
    try:
        # Build index if not already done
        build_sloka_search_index()

        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: text'}), 400

        query_text = data['text'].strip()
        if not query_text:
            return jsonify({'success': False, 'error': 'Search text cannot be empty'}), 400

        threshold = float(data.get('threshold', 0.7))
        limit = min(int(data.get('limit', 10)), 50)  # Cap at 50 results

        # Normalize query for comparison
        query_normalized = normalize_sanskrit_text(query_text)

        if not query_normalized:
            return jsonify({'success': False, 'error': 'Query text is empty after normalization'}), 400

        # Search through all slokas
        matches = []

        for sloka_data in _sloka_search_cache['slokas']:
            # Calculate similarity on normalized text
            similarity = calculate_similarity(query_normalized, sloka_data['normalized'])

            if similarity >= threshold:
                matches.append(
                    {
                        'original_text': sloka_data['text'],
                        'dataset_id': sloka_data['dataset_id'],
                        'dataset_name': sloka_data['dataset_name'],
                        'chandas': sloka_data['chandas'],
                        'source': sloka_data['source'],
                        'similarity': round(similarity, 4),
                        'is_exact_match': similarity >= 0.99,
                    }
                )

        # Sort by similarity descending
        matches.sort(key=lambda x: x['similarity'], reverse=True)

        # Limit results
        matches = matches[:limit]

        # Determine if input appears to have errors
        has_exact_match = any(m['is_exact_match'] for m in matches)
        best_match = matches[0] if matches else None

        # Generate diff hints for the best match
        diff_hints = []
        if best_match and not best_match['is_exact_match']:
            # Simple character-level diff hints
            original = best_match['original_text']
            query = query_text

            # Find potential differences
            if len(query) != len(original):
                diff_hints.append(
                    f"Length difference: your input has {len(query)} chars, original has {len(original)} chars"
                )

        return jsonify(
            {
                'success': True,
                'query': query_text,
                'query_normalized': query_normalized,
                'matches': matches,
                'match_count': len(matches),
                'has_exact_match': has_exact_match,
                'best_similarity': best_match['similarity'] if best_match else 0,
                'diff_hints': diff_hints,
                'total_slokas_indexed': len(_sloka_search_cache['slokas']),
            }
        )

    except ValueError as e:
        return jsonify({'success': False, 'error': f'Invalid parameter: {e}'}), 400
    except Exception as e:
        logger.exception(f"Error in sloka search: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/sloka/validate', methods=['POST'])
def validate_sloka():
    """
    Validate a sloka and identify specific errors/differences from the dataset.
    Uses difflib for smart diff that doesn't cascade errors.

    Request JSON:
        {
            "text": "Sloka text to validate"
        }

    Returns:
        JSON with validation results including:
        - highlighted_text: User's text with error positions marked
        - differences: List of actual differences (not cascading)
    """
    text_payload()
    try:
        import difflib

        # Build index if not already done
        build_sloka_search_index()

        data = request.get_json()

        if not data or 'text' not in data:
            return jsonify({'success': False, 'error': 'Missing required field: text'}), 400

        query_text = data['text'].strip()
        if not query_text:
            return jsonify({'success': False, 'error': 'Text cannot be empty'}), 400

        # Normalize query for finding best match
        query_normalized = normalize_sanskrit_text(query_text)

        # Find best match using similarity
        best_match = None
        best_similarity = 0

        for sloka_data in _sloka_search_cache['slokas']:
            similarity = calculate_similarity(query_normalized, sloka_data['normalized'])
            if similarity > best_similarity:
                best_similarity = similarity
                best_match = sloka_data

        if not best_match or best_similarity < 0.5:
            return jsonify(
                {
                    'success': True,
                    'found': False,
                    'message': 'No similar sloka found in the database. This verse may not be in our collection.',
                    'query': query_text,
                }
            )

        original = best_match['text']

        # Normalize both texts for comparison (remove line breaks, extra spaces)
        # but keep track of original for display
        query_clean = ' '.join(query_text.split())
        original_clean = ' '.join(original.split())

        # If user's input is shorter, they might have entered partial sloka
        # In that case, only compare up to user's input length in original
        # Find the best matching substring in original
        if len(query_clean) < len(original_clean) * 0.7:
            # User entered a partial sloka - find the matching portion
            # Use get_close_matches on chunks to find best alignment
            matcher = difflib.SequenceMatcher(None, query_clean, original_clean)

            # Find longest matching block
            blocks = matcher.get_matching_blocks()
            if blocks:
                # Take the portion of original that aligns with user input
                # For simplicity, compare from the beginning
                original_portion = original_clean[: len(query_clean) + 20]  # Add some buffer
            else:
                original_portion = original_clean
        else:
            original_portion = original_clean

        # Use SequenceMatcher to find the real differences
        matcher = difflib.SequenceMatcher(None, query_clean, original_portion)

        # Get the opcodes which tell us what operations transform query into original
        opcodes = matcher.get_opcodes()

        differences = []
        error_positions = set()  # Track positions in user's text that are wrong

        for tag, i1, i2, j1, j2 in opcodes:
            if tag == 'equal':
                # These characters match, no error
                continue
            elif tag == 'replace':
                # Characters at these positions are different
                user_segment = query_clean[i1:i2]
                correct_segment = original_portion[j1:j2]
                differences.append(
                    {
                        'type': 'replace',
                        'position': i1,
                        'end_position': i2,
                        'your_text': user_segment,
                        'correct_text': correct_segment,
                        'description': f"'{user_segment}' should be '{correct_segment}'",
                    }
                )
                # Mark all positions in this range as errors
                for pos in range(i1, i2):
                    error_positions.add(pos)
            elif tag == 'delete':
                # Extra characters in user's input (not in original)
                extra_segment = query_clean[i1:i2]
                differences.append(
                    {
                        'type': 'extra',
                        'position': i1,
                        'end_position': i2,
                        'your_text': extra_segment,
                        'correct_text': '',
                        'description': f"Extra: '{extra_segment}'",
                    }
                )
                for pos in range(i1, i2):
                    error_positions.add(pos)
            elif tag == 'insert':
                # Missing characters (in original but not in user's input)
                missing_segment = original_portion[j1:j2]
                # Only report missing if it's not just trailing text (user entered partial)
                if i1 < len(query_clean) - 5:  # Not at the end
                    differences.append(
                        {
                            'type': 'missing',
                            'position': i1,
                            'end_position': i1,
                            'your_text': '',
                            'correct_text': missing_segment,
                            'description': f"Missing: '{missing_segment}'",
                        }
                    )

        # Build highlighted segments for the frontend
        # Each segment is either normal or an error
        highlighted_segments = []

        i = 0
        while i < len(query_clean):
            if i in error_positions:
                # Find the end of this error run
                start = i
                while i < len(query_clean) and i in error_positions:
                    i += 1
                highlighted_segments.append({'text': query_clean[start:i], 'isError': True})
            else:
                # Find the end of this normal run
                start = i
                while i < len(query_clean) and i not in error_positions:
                    i += 1
                highlighted_segments.append({'text': query_clean[start:i], 'isError': False})

        is_valid = len(differences) == 0

        # Recalculate similarity on cleaned texts for more accurate percentage
        final_similarity = difflib.SequenceMatcher(None, query_clean, original_clean).ratio()

        return jsonify(
            {
                'success': True,
                'found': True,
                'is_valid': is_valid,
                'similarity': round(final_similarity, 4),
                'similarity_percentage': round(final_similarity * 100, 1),
                'original_text': original,  # Keep original with line breaks for display
                'your_text': query_text,
                'highlighted_segments': highlighted_segments,
                'chandas': best_match['chandas'],
                'dataset_name': best_match['dataset_name'],
                'source': best_match['source'],
                'differences': differences,
                'difference_count': len(differences),
                'message': 'Perfect match!' if is_valid else f'Found {len(differences)} difference(s).',
            }
        )

    except Exception as e:
        logger.exception(f"Error in sloka validation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
