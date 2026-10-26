"""Meter identification routes: plain text, daṇḍaka mode and uploaded documents."""

import logging
import time
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend.api.helpers import ALLOWED_DOCUMENT_EXTENSIONS, allowed_file, request_upload_path
from backend.api.schemas import DandakaRequest, IdentifyTextRequest
from backend.api.validation import parse_body
from backend.api.verse_search import CACHE_CLOSE_MATCH_THRESHOLD, find_cached_verse_match
from backend.config import settings
from backend.core.ai_validator import validate_shloka_input
from backend.utils.file_processor import FileProcessingError, get_processor

logger = logging.getLogger(__name__)

bp = Blueprint('identify', __name__)


def downloadable_result(paths):
    """File name /download serves for an analysis: the saved JSON result, or None if nothing was saved."""
    if isinstance(paths, dict):
        return paths.get('json')
    if isinstance(paths, Path):
        return paths.name
    return paths or None


@bp.route(f'{settings.API_PREFIX}/identify/text', methods=['POST'])
def identify_text():
    """
    Identify meter from plain text.

    Request JSON:
        {
            "text": "Sanskrit text in Devanagari or other scheme",
            "output_scheme": "devanagari|iast|itrans|...",
            "text_mode": "verse|line",
            "identification_mode": "auto|vedic|classical",
            "enable_sandhi": true|false
        }

    identification_mode options:
        - auto: Smart detection (default) - tries both and picks best
        - vedic: For Rigveda/Vedic texts - syllable-count based identification
        - classical: For Kavya/classical poetry - L-G pattern based identification

    Returns:
        JSON with identified meters and analysis results
    """
    body = parse_body(IdentifyTextRequest)
    try:
        text = body.text
        output_scheme = body.output_scheme
        text_mode = body.effective_text_mode
        enable_sandhi = body.enable_sandhi
        identification_mode = body.identification_mode
        verse_mode = text_mode == 'verse'

        # Start timing for latency measurement
        start_time = time.time()
        timing_info = {
            'total_ms': 0,
            'cache_lookup_ms': 0,
            'ai_validation_ms': 0,
            'rule_engine_ms': 0,
            'cache_hit': False,
            'ai_skipped': False,
        }

        logger.info(f"Analyzing text (text_mode: {text_mode}, id_mode: {identification_mode}, sandhi: {enable_sandhi})")

        # =====================================================================
        # STEP 1: VERSE CACHE LOOKUP - Check if we have this verse already
        # If found with high similarity, skip AI validation entirely
        # =====================================================================
        cache_start = time.time()
        cache_result = find_cached_verse_match(text, threshold=CACHE_CLOSE_MATCH_THRESHOLD)
        timing_info['cache_lookup_ms'] = round((time.time() - cache_start) * 1000, 2)

        skip_ai = cache_result.get('skip_ai', False)
        timing_info['cache_hit'] = cache_result.get('found', False)
        timing_info['ai_skipped'] = skip_ai

        if cache_result.get('found'):
            logger.info(f"Cache hit! Similarity: {cache_result['similarity']:.2%}, Skip AI: {skip_ai}")

        # =====================================================================
        # STEP 2: AI PRE-VALIDATION (skipped if cache hit with high similarity)
        # This prevents the rule-based model from predicting invalid chandas
        # =====================================================================
        ai_validation = {'ai_validated': False, 'text_type': 'unknown', 'confidence': 0.0}

        if skip_ai:
            # Cache hit - assume valid Sanskrit (it's in our verified dataset)
            logger.info("Skipping AI validation - verse found in cache")
            should_proceed = True
            ai_validation = {
                'ai_validated': False,
                'text_type': 'verse',
                'confidence': cache_result.get('similarity', 0.9),
                'skipped_reason': 'cache_hit',
            }
        else:
            # No cache hit - run AI validation
            ai_start = time.time()
            should_proceed, rejection_reason, ai_validation = validate_shloka_input(text, skip_ai=False)
            timing_info['ai_validation_ms'] = round((time.time() - ai_start) * 1000, 2)

        if not should_proceed:
            logger.info(f"AI validation rejected input: {rejection_reason}")
            timing_info['total_ms'] = round((time.time() - start_time) * 1000, 2)

            # Return a 200 OK with invalid input result (same format as chanda.py)
            # This allows the frontend to display it nicely instead of as an error
            invalid_result = {
                'line': [
                    {
                        'line': text,
                        'result': {
                            'found': False,
                            'is_padya': False,
                            'is_valid_input': False,
                            'validation_error': 'Invalid Sanskrit input',
                            'prose_message': 'Please enter valid Sanskrit text using Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)',
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
                            'fuzzy': [],
                        },
                    }
                ]
            }

            return jsonify(
                {
                    'success': True,  # Return success so frontend doesn't show error box
                    'result': invalid_result,
                    'summary': {
                        'count': {'line': 1, 'match_line': 0},
                        'line': {'match': {'chanda': {}}, 'no_match': 1},
                    },
                    'summary_formatted': 'Invalid input - not Sanskrit text',
                    'is_valid_input': False,
                    'validation_message': 'Please enter valid Sanskrit text using Devanagari (देवनागरी) or IAST with diacritics (dharmakṣetre)',
                    'timing': timing_info,
                }
            )
        # =====================================================================

        # =====================================================================
        # STEP 3: METER IDENTIFICATION (rule engine)
        # =====================================================================
        rule_start = time.time()
        result = current_app.chanda.identify_from_text(
            text,
            verse=verse_mode,
            fuzzy=True,
            save_path=settings.RESULTS_DIR,
            scheme=output_scheme,
            use_sandhi=enable_sandhi,
            mode=identification_mode,
        )
        timing_info['rule_engine_ms'] = round((time.time() - rule_start) * 1000, 2)
        timing_info['total_ms'] = round((time.time() - start_time) * 1000, 2)

        # Generate summary
        summary = current_app.chanda.summarize_results(result['result'])
        summary_formatted = current_app.chanda.format_summary(summary)

        # Handle result path
        result_path = downloadable_result(result.get('path'))

        # Log timing summary
        if timing_info['cache_hit']:
            ai_status = 'SKIPPED' if timing_info['ai_skipped'] else f"{timing_info['ai_validation_ms']}ms"
            logger.info(
                f"[TIMING] Cache HIT | Total: {timing_info['total_ms']}ms | Cache: {timing_info['cache_lookup_ms']}ms | AI: {ai_status} | Rule: {timing_info['rule_engine_ms']}ms"
            )
        else:
            logger.info(
                f"[TIMING] Cache MISS | Total: {timing_info['total_ms']}ms | Cache: {timing_info['cache_lookup_ms']}ms | AI: {timing_info['ai_validation_ms']}ms | Rule: {timing_info['rule_engine_ms']}ms"
            )

        return jsonify(
            {
                'success': True,
                'result': result['result'],
                'result_path': result_path,
                'summary': summary,
                'summary_formatted': summary_formatted,
                'ai_validation': {
                    'validated': ai_validation.get('ai_validated', False),
                    'text_type': ai_validation.get('text_type', 'unknown'),
                    'confidence': ai_validation.get('confidence', 0.0),
                    'skipped': timing_info['ai_skipped'],
                },
                'cache_info': {
                    'hit': timing_info['cache_hit'],
                    'similarity': cache_result.get('similarity', 0.0) if cache_result.get('found') else 0.0,
                    'cached_chandas': cache_result.get('cached_data', {}).get('chandas', '')
                    if cache_result.get('found')
                    else '',
                    'source_dataset': cache_result.get('cached_data', {}).get('dataset', '')
                    if cache_result.get('found')
                    else '',
                },
                'timing': timing_info,
                'input': {
                    'text': text,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'identification_mode': identification_mode,
                    'enable_sandhi': enable_sandhi,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error in identify_text: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/identify/dandaka', methods=['POST'])
def identify_dandaka():
    """
    Identify Dandaka verses and Rajashyamala Stotram.

    Request JSON:
        {
            "text": "Sanskrit text in Devanagari or other scheme"
        }

    Returns:
        JSON with dandaka and rajashyamala analysis results
    """
    text = parse_body(DandakaRequest).text
    try:
        from backend.core.dandaka_detector import analyze_dandaka_mode

        logger.info("Analyzing text in Dandaka mode")

        # Call the dandaka analyzer
        result = analyze_dandaka_mode(text)

        return jsonify({'success': True, 'result': result})

    except Exception as e:
        logger.exception(f"Error in identify_dandaka: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/identify/file', methods=['POST'])
def identify_file():
    """
    Identify meter from an uploaded document file.

    Supports: PDF (text-based), DOCX, TXT
    Max file size: 10MB

    Request: Multipart form data with 'text_file' field
    Additional fields:
        output_scheme: transliteration scheme
        text_mode: "verse" or "line"
        enable_sandhi: boolean
    """
    try:
        if 'text_file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided', 'error_code': 'NO_FILE'}), 400

        file = request.files['text_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename', 'error_code': 'EMPTY_FILENAME'}), 400

        # Check extension first (fast validation)
        if not allowed_file(file.filename, ALLOWED_DOCUMENT_EXTENSIONS):
            return jsonify(
                {
                    'success': False,
                    'error': 'Unsupported file type. Allowed: PDF, DOCX, TXT',
                    'error_code': 'INVALID_TYPE',
                }
            ), 400

        # Save uploaded file
        filename = secure_filename(file.filename)
        filepath = request_upload_path(filename)
        file.save(filepath)

        # Use file processor for text extraction
        processor = get_processor()

        try:
            extraction_result = processor.process_file(filepath, validate_sanskrit=True)
        except FileProcessingError as e:
            return jsonify(
                {'success': False, 'error': e.message, 'error_code': e.error_code, 'details': e.details}
            ), 400

        text = extraction_result.text

        # Get parameters
        output_scheme = request.form.get('output_scheme', None)
        text_mode = request.form.get('text_mode', 'line')
        enable_sandhi = request.form.get('enable_sandhi', 'false').lower() == 'true'
        identification_mode = request.form.get('identification_mode', 'auto')

        logger.info(
            f"Analyzing file: {filename} ({extraction_result.file_type.value}, {extraction_result.page_count} pages)"
        )

        # NOTE: AI validation is SKIPPED for file uploads (batch mode)
        # This is intentional to save API quota and reduce latency for large files
        # The rule-based validation in chanda.py still applies

        # Perform meter identification
        verse_mode = text_mode == 'verse'
        result = current_app.chanda.identify_from_text(
            text,
            verse=verse_mode,
            fuzzy=True,
            save_path=settings.RESULTS_DIR,
            scheme=output_scheme,
            use_sandhi=enable_sandhi,
            mode=identification_mode,
        )

        # Generate summary
        summary = current_app.chanda.summarize_results(result['result'])
        summary_formatted = current_app.chanda.format_summary(summary)

        # Handle result path
        result_path = downloadable_result(result.get('path'))

        return jsonify(
            {
                'success': True,
                'text': text,
                'result': result['result'],
                'result_path': result_path,
                'summary': summary,
                'summary_formatted': summary_formatted,
                'file_info': {
                    'filename': filename,
                    'file_type': extraction_result.file_type.value,
                    'page_count': extraction_result.page_count,
                    'encoding': extraction_result.encoding,
                },
                'input': {
                    'filename': filename,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'enable_sandhi': enable_sandhi,
                    'identification_mode': identification_mode,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error in identify_file: {e}")
        return jsonify({'success': False, 'error': str(e), 'error_code': 'INTERNAL_ERROR'}), 500


@bp.route(f'{settings.API_PREFIX}/download/<filename>', methods=['GET'])
def download_result(filename):
    """
    Download a result file.

    Args:
        filename: Name of the file to download
    """
    try:
        return send_from_directory(settings.RESULTS_DIR, filename, as_attachment=True)
    except Exception as e:
        logger.exception(f"Error downloading file: {e}")
        return jsonify({'error': 'File not found'}), 404
