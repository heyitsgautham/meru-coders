"""Turning the chat route's audio and image attachments into text.

Both helpers take the attachment as a base64 string, optionally a data URL,
and either return the text or raise ChatInputError with the message and HTTP
status the route answers with.
"""

import base64
import io
import logging

logger = logging.getLogger(__name__)

# Google Cloud Speech is optional; without it audio attachments answer 500.
try:
    from google.cloud import speech_v1 as gcp_speech

    SPEECH_AVAILABLE = True
except ImportError:
    SPEECH_AVAILABLE = False
    gcp_speech = None

SPEECH_UNAVAILABLE = 'Audio transcription service is not available. Please use text or image input.'
MIN_IMAGE_BYTES = 100


class ChatInputError(Exception):
    """An attachment the chat route cannot use; carries the user-facing message and status."""

    def __init__(self, message: str, status: int):
        super().__init__(message)
        self.message = message
        self.status = status


def decode_base64_payload(data: str) -> bytes:
    """Bytes of a base64 string, dropping a data URL prefix such as 'data:image/png;base64,'."""
    if ',' in data:
        data = data.split(',', 1)[1]
    return base64.b64decode(data)


def _recognize(client, audio, encoding):
    config = gcp_speech.RecognitionConfig(
        encoding=encoding,
        **({'sample_rate_hertz': 48000} if encoding == gcp_speech.RecognitionConfig.AudioEncoding.WEBM_OPUS else {}),
        language_code="en-US",  # Primary language hint
        alternative_language_codes=["hi-IN", "sa-IN"],  # Hindi and Sanskrit alternatives
        enable_automatic_punctuation=True,
        model="latest_long",
    )
    return client.recognize(config=config, audio=audio)


def transcribe_audio(audio_data: str) -> str:
    """Speech-to-text for a browser recording: WebM/Opus first, then the encoding Google detects."""
    try:
        logger.info("Processing audio with speech-to-text...")
        audio_bytes = decode_base64_payload(audio_data)
        logger.info(f"Audio decoded, size: {len(audio_bytes)} bytes")

        if not SPEECH_AVAILABLE or gcp_speech is None:
            logger.error("Google Cloud Speech is not available")
            raise ChatInputError(SPEECH_UNAVAILABLE, 500)

        try:
            client = gcp_speech.SpeechClient()
            audio = gcp_speech.RecognitionAudio(content=audio_bytes)
            encodings = gcp_speech.RecognitionConfig.AudioEncoding
            try:
                logger.info("Attempting speech recognition with language detection...")
                response = _recognize(client, audio, encodings.WEBM_OPUS)
                if not response.results:
                    logger.warning("No results with WEBM_OPUS, trying auto-detect encoding...")
                    response = _recognize(client, audio, encodings.ENCODING_UNSPECIFIED)
                if not response.results:
                    logger.warning("Speech-to-Text found no speech in audio")
                    raise ChatInputError(
                        'Could not understand the audio. Please speak clearly or use text/image input.', 400
                    )
                if response.results[0].language_code:
                    logger.info(f"Detected language: {response.results[0].language_code}")
                text = ' '.join([result.alternatives[0].transcript for result in response.results])
                logger.info(f"Speech-to-Text extracted: {text}")
                return text
            except ChatInputError:
                raise
            except Exception as recognition_error:
                logger.error(f"Recognition error: {str(recognition_error)}")
                raise ChatInputError(
                    'Audio transcription failed. Please try again or use text/image input.', 500
                ) from recognition_error
        except ChatInputError:
            raise
        except Exception as stt_error:
            logger.error(f"Speech-to-Text error: {str(stt_error)}")
            raise ChatInputError(SPEECH_UNAVAILABLE, 500) from stt_error
    except ChatInputError:
        raise
    except Exception as audio_error:
        logger.error(f"Audio processing error: {str(audio_error)}")
        raise ChatInputError(f'Error processing audio: {str(audio_error)}', 500) from audio_error


def extract_image_text(image_data: str, app) -> str:
    """OCR for an image attachment through the app's Cloud Vision reader, or Tesseract as the fallback."""
    try:
        logger.info("Processing image with OCR...")
        image_bytes = decode_base64_payload(image_data)
        logger.info(f"Image decoded, size: {len(image_bytes)} bytes")

        if len(image_bytes) < MIN_IMAGE_BYTES:
            raise ChatInputError('Image data appears to be invalid or corrupted. Please try uploading again.', 400)

        if getattr(app, 'cloud_vision_ocr', None):
            logger.info("Using Google Cloud Vision OCR...")
            text = app.cloud_vision_ocr.extract_text_from_bytes(image_bytes).strip()
            logger.info(f"Cloud Vision OCR extracted {len(text)} characters")
        elif getattr(app, 'tesseract_ocr', None):
            logger.info("Using Tesseract OCR (fallback)...")
            import PIL.Image

            image = PIL.Image.open(io.BytesIO(image_bytes))
            text = app.tesseract_ocr.extract_text(image).get('text', '').strip()
            logger.info(f"Tesseract OCR extracted {len(text)} characters")
        else:
            logger.error("No OCR service available")
            raise ChatInputError('OCR service is not available. Please contact support.', 500)

        if not text:
            logger.warning("OCR extracted no text from image")
            raise ChatInputError(
                'Could not extract any text from the image. '
                'Please ensure the image contains clear, readable Sanskrit text.',
                400,
            )
        return text
    except ChatInputError:
        raise
    except Exception as ocr_error:
        logger.error(f"OCR processing error: {str(ocr_error)}")
        raise ChatInputError(f'Error processing image: {str(ocr_error)}', 500) from ocr_error
