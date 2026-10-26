"""Routes that read text out of images and documents before identification."""

import base64
import logging
from pathlib import Path

from flask import Blueprint, current_app, jsonify, request
from werkzeug.utils import secure_filename

from backend.api.helpers import ALLOWED_DOCUMENT_EXTENSIONS, allowed_file, request_upload_path
from backend.config import settings
from backend.utils.file_processor import FileProcessingError, get_processor

logger = logging.getLogger(__name__)

bp = Blueprint('ocr_routes', __name__)


@bp.route(f'{settings.API_PREFIX}/identify/image', methods=['POST'])
def identify_image():
    """
    Identify meter from an image containing Sanskrit text.

    Request can be:
    1. Multipart form data with 'image_file' field
    2. JSON with base64 encoded image in 'image_data' field

    Additional fields:
        ocr_engine: "tesseract" or "google"
        output_scheme: transliteration scheme
        text_mode: "verse" or "line"
        enable_sandhi: boolean
    """
    try:
        # Get OCR engine preference
        identification_mode = 'auto'  # Default
        if request.is_json:
            data = request.get_json()
            ocr_engine = data.get('ocr_engine', 'tesseract')
            output_scheme = data.get('output_scheme', None)
            text_mode = data.get('text_mode', 'line')
            enable_sandhi = data.get('enable_sandhi', False)
            identification_mode = data.get('identification_mode', 'auto')

            # Handle base64 encoded image
            if 'image_data' in data:
                image_data = data['image_data']
                # Remove data URL prefix if present
                if ',' in image_data:
                    image_data = image_data.split(',', 1)[1]

                # Decode and save
                image_bytes = base64.b64decode(image_data)
                filename = 'uploaded_image.png'
                filepath = request_upload_path(filename)
                filepath.write_bytes(image_bytes)
            else:
                return jsonify({'error': 'Missing image_data in JSON request'}), 400
        else:
            # Handle multipart form data
            if 'image_file' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400

            file = request.files['image_file']
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400

            if not allowed_file(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS):
                return jsonify({'error': f'Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}'}), 400

            filename = secure_filename(file.filename)
            filepath = request_upload_path(filename)
            file.save(filepath)

            ocr_engine = request.form.get('ocr_engine', 'tesseract')
            output_scheme = request.form.get('output_scheme', None)
            text_mode = request.form.get('text_mode', 'line')
            enable_sandhi = request.form.get('enable_sandhi', 'false').lower() == 'true'
            identification_mode = request.form.get('identification_mode', 'auto')

        # Perform OCR - Cloud Vision first, fallback to Tesseract
        text = None
        engine_used = None

        if current_app.cloud_vision_ocr:
            try:
                text = current_app.cloud_vision_ocr.extract_text(filepath)
                engine_used = 'cloud_vision'
            except Exception as e:
                logger.warning(f"Cloud Vision OCR failed, falling back to Tesseract: {e}")

        if text is None and current_app.tesseract_ocr:
            try:
                text = current_app.tesseract_ocr.extract_text(filepath)
                engine_used = 'tesseract'
            except Exception as e:
                logger.error(f"Tesseract OCR also failed: {e}")
                return jsonify({'success': False, 'error': f'OCR extraction failed: {e}'}), 500

        if text is None:
            return jsonify({'error': 'No OCR engine available'}), 503

        logger.info(f"Extracted text via {engine_used}: {text[:100] if text else '(empty)'}...")

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
        result_path = None
        if result.get('path'):
            if isinstance(result['path'], Path):
                result_path = result['path'].name
            else:
                result_path = str(result['path'])

        # Encode image for response
        with open(filepath, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')

        return jsonify(
            {
                'success': True,
                'text': text,
                'result': result['result'],
                'result_path': result_path,
                'summary': summary,
                'summary_formatted': summary_formatted,
                'image_data': image_base64,
                'input': {
                    'ocr_engine': ocr_engine,
                    'output_scheme': output_scheme,
                    'text_mode': text_mode,
                    'enable_sandhi': enable_sandhi,
                    'identification_mode': identification_mode,
                },
            }
        )

    except Exception as e:
        logger.exception(f"Error in identify_image: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/ocr/extract', methods=['POST'])
def ocr_extract():
    """
    Extract text from an image using OCR only (no meter analysis).

    Uses Cloud Vision OCR as primary, falls back to Tesseract if unavailable.

    Request: Multipart form data with 'image_file' field

    Returns:
        JSON with extracted text only
    """
    try:
        # Handle multipart form data
        if 'image_file' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400

        file = request.files['image_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400

        if not allowed_file(file.filename, settings.ALLOWED_IMAGE_EXTENSIONS):
            return jsonify(
                {'success': False, 'error': f'Invalid file type. Allowed: {settings.ALLOWED_IMAGE_EXTENSIONS}'}
            ), 400

        filename = secure_filename(file.filename)
        filepath = request_upload_path(filename)
        file.save(filepath)

        logger.info(f"OCR extraction requested for: {filename}")

        # Try Cloud Vision first, fallback to Tesseract
        text = None
        engine_used = None

        if current_app.cloud_vision_ocr:
            try:
                text = current_app.cloud_vision_ocr.extract_text(filepath)
                engine_used = 'cloud_vision'
                logger.info(f"Cloud Vision OCR extracted {len(text)} characters")
            except Exception as e:
                logger.warning(f"Cloud Vision OCR failed, falling back to Tesseract: {e}")

        if text is None and current_app.tesseract_ocr:
            try:
                text = current_app.tesseract_ocr.extract_text(filepath)
                engine_used = 'tesseract'
                logger.info(f"Tesseract OCR extracted {len(text)} characters")
            except Exception as e:
                logger.error(f"Tesseract OCR also failed: {e}")
                return jsonify({'success': False, 'error': f'OCR extraction failed: {e}'}), 500

        if text is None:
            return jsonify({'success': False, 'error': 'No OCR engine available'}), 503

        logger.info(f"OCR extraction complete via {engine_used}: {len(text)} chars")

        return jsonify({'success': True, 'text': text})

    except Exception as e:
        logger.exception(f"Error in ocr_extract: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/file/extract', methods=['POST'])
def extract_file():
    """
    Extract text from a document file (no meter analysis).

    Supports: PDF (text-based), DOCX, TXT
    Max file size: 10MB

    Request: Multipart form data with 'file' field

    Returns:
        JSON with extracted text and file info
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided', 'error_code': 'NO_FILE'}), 400

        file = request.files['file']
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

        logger.info(f"Extracting text from file: {filename}")

        # Use file processor for text extraction
        processor = get_processor()

        try:
            extraction_result = processor.process_file(filepath, validate_sanskrit=True)
        except FileProcessingError as e:
            return jsonify(
                {'success': False, 'error': e.message, 'error_code': e.error_code, 'details': e.details}
            ), 400

        logger.info(f"Extracted {len(extraction_result.text)} characters from {filename}")

        response_data = {
            'success': True,
            'text': extraction_result.text,
            'file_info': {
                'filename': filename,
                'file_type': extraction_result.file_type.value,
                'page_count': extraction_result.page_count,
                'encoding': extraction_result.encoding,
            },
        }

        # Include warnings if any (e.g., CID encoding issues)
        if extraction_result.warnings:
            response_data['warnings'] = extraction_result.warnings

        return jsonify(response_data)

    except Exception as e:
        logger.exception(f"Error in extract_file: {e}")
        return jsonify({'success': False, 'error': str(e), 'error_code': 'INTERNAL_ERROR'}), 500
