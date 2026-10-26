"""Text-to-speech and speech-to-text routes."""

import asyncio
import logging
import re
import shutil
import tempfile
import uuid
from pathlib import Path

from flask import Blueprint, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename

from backend.api.helpers import allowed_file
from backend.api.schemas import TTSRequest
from backend.api.validation import parse_body
from backend.config import settings

# Import edge-tts for text-to-speech functionality
try:
    import edge_tts

    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("edge-tts not available. TTS functionality will be disabled.")

# Import gTTS as fallback
try:
    from gtts import gTTS

    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS not available. Fallback TTS will be disabled.")

# Import Google Cloud TTS (best quality with voice selection)
try:
    from google.cloud import texttospeech

    GOOGLE_TTS_AVAILABLE = True
    logging.info("Google Cloud TTS library imported successfully")
except ImportError:
    GOOGLE_TTS_AVAILABLE = False
    logging.warning("Google Cloud TTS not available - install with: pip install google-cloud-texttospeech")

# Import pyttsx3 (offline TTS with voice selection)
try:
    import pyttsx3  # noqa: F401 - availability probe

    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available.")


logger = logging.getLogger(__name__)

bp = Blueprint('speech', __name__)


# Names generate_tts gives its output: the only files /tts/audio/ will serve.
TTS_FILENAME = re.compile(r'tts_[0-9a-f]{32}\.mp3')


@bp.route(f'{settings.API_PREFIX}/tts/generate', methods=['POST'])
def generate_tts():
    """
    Generate text-to-speech audio for Sanskrit/Hindi text.

    Request JSON:
        {
            "text": "Sanskrit text to convert to speech",
            "voice": "male|female" // (optional, defaults to "female")
        }

    Returns:
        JSON with audio file URL
    """
    if not EDGE_TTS_AVAILABLE and not GTTS_AVAILABLE and not GOOGLE_TTS_AVAILABLE and not PYTTSX3_AVAILABLE:
        return jsonify(
            {
                'success': False,
                'error': 'Text-to-speech functionality is not available. Please install edge-tts, gTTS, pyttsx3, or google-cloud-texttospeech.',
            }
        ), 503

    body = parse_body(TTSRequest)
    try:
        text = body.text.strip()
        if not text:
            return jsonify({'success': False, 'error': 'Text cannot be empty'}), 400

        logger.info(f"TTS request received - text length: {len(text)} chars")

        # Voice selection
        voice_type = body.voice
        logger.info(f"TTS voice requested: {voice_type}")

        # Generate unique filename
        filename = f"tts_{uuid.uuid4().hex}.mp3"
        output_path = settings.AUDIO_DIR / filename

        # Ensure audio directory exists
        settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)

        # Try Google Cloud TTS first (best quality with proper voice selection)
        generation_success = False
        used_engine = None

        if GOOGLE_TTS_AVAILABLE:
            try:
                logger.info("Attempting TTS generation with Google Cloud TTS...")
                client = texttospeech.TextToSpeechClient()

                # Configure voice selection - Google Cloud TTS with Chirp3-HD voices for Sanskrit
                voice_configs = {
                    "male": {
                        "language_code": "hi-IN",
                        "name": "hi-IN-Chirp3-HD-Algieba",  # Male Chirp3-HD voice for Sanskrit
                        "ssml_gender": texttospeech.SsmlVoiceGender.MALE,
                    },
                    "female": {
                        "language_code": "hi-IN",
                        "name": "hi-IN-Wavenet-A",  # Female voice (Google Cloud TTS)
                        "ssml_gender": texttospeech.SsmlVoiceGender.FEMALE,
                    },
                }

                voice_config = voice_configs.get(voice_type, voice_configs['male'])

                # Set up synthesis input
                synthesis_input = texttospeech.SynthesisInput(text=text)

                # Select voice parameters
                voice = texttospeech.VoiceSelectionParams(
                    language_code=voice_config["language_code"],
                    name=voice_config["name"],
                    ssml_gender=voice_config["ssml_gender"],
                )

                # Select audio config
                audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3)

                # Perform TTS request
                response = client.synthesize_speech(input=synthesis_input, voice=voice, audio_config=audio_config)

                # Write audio to file
                with open(str(output_path), 'wb') as out:
                    out.write(response.audio_content)

                if output_path.exists() and output_path.stat().st_size > 0:
                    generation_success = True
                    used_engine = f"Google Cloud TTS ({voice_config['name']})"
                    logger.info(f"TTS generated successfully with Google Cloud TTS ({voice_type} voice)")
                else:
                    logger.warning("Google Cloud TTS created empty file")
                    if output_path.exists():
                        output_path.unlink()
            except Exception as e:
                logger.warning(f"Google Cloud TTS failed: {e}. Falling back to edge-tts...")
                if output_path.exists():
                    output_path.unlink()

        # Try edge-tts second, fallback to gTTS
        if not generation_success and EDGE_TTS_AVAILABLE:
            try:
                logger.info("Attempting TTS generation with edge-tts...")
                # Hindi neural voices work well for Sanskrit
                voices = {"female": "hi-IN-SwaraNeural", "male": "hi-IN-MadhurNeural"}
                voice = voices.get(voice_type, voices['male'])
                logger.info(f"TTS using edge-tts voice: {voice}")

                async def generate_speech():
                    communicate = edge_tts.Communicate(text, voice)
                    await communicate.save(str(output_path))

                # Run async function
                asyncio.run(generate_speech())

                # Check if file was created successfully
                if output_path.exists() and output_path.stat().st_size > 0:
                    generation_success = True
                    used_engine = "edge-tts"
                    logger.info("TTS generated successfully with edge-tts")
                else:
                    logger.warning("edge-tts created empty file, falling back to gTTS")
                    if output_path.exists():
                        output_path.unlink()
            except Exception as e:
                logger.warning(f"edge-tts failed: {e}. Falling back to gTTS...")
                if output_path.exists():
                    output_path.unlink()

        # Fallback to gTTS if edge-tts failed or not available
        if not generation_success and GTTS_AVAILABLE:
            try:
                logger.info(f"Attempting TTS generation with gTTS (voice: {voice_type})...")
                # gTTS doesn't support different voices natively, but we can adjust parameters
                # Use 'hi' for Hindi which works well for Sanskrit
                # Note: gTTS uses a single voice per language, so male/female selection isn't supported
                # We'll use slow=False for male (normal speed) and could adjust other params
                tts = gTTS(text=text, lang='hi', slow=False)
                tts.save(str(output_path))

                if output_path.exists() and output_path.stat().st_size > 0:
                    generation_success = True
                    used_engine = "gTTS (Note: Voice selection not supported in fallback mode)"
                    logger.info("TTS generated successfully with gTTS")
                    logger.warning("gTTS doesn't support voice selection - using default Hindi voice")
            except Exception as e:
                logger.error(f"gTTS also failed: {e}")
                if output_path.exists():
                    output_path.unlink()

        # Verify file was created and has content
        if not generation_success or not output_path.exists():
            logger.error("Audio file was not created")
            return jsonify({'success': False, 'error': 'Failed to generate audio file with all available engines'}), 500

        file_size = output_path.stat().st_size
        if file_size == 0:
            logger.error(f"Audio file is empty: {output_path}")
            output_path.unlink()  # Clean up empty file
            return jsonify({'success': False, 'error': 'Generated audio file is empty'}), 500

        logger.info(f"TTS audio generated successfully using {used_engine}: {filename} ({file_size} bytes)")

        return jsonify(
            {
                'success': True,
                'audio_url': f'{settings.API_PREFIX}/tts/audio/{filename}',
                'filename': filename,
                'engine': used_engine,
                'voice': voice_type,
            }
        )

    except Exception as e:
        logger.exception(f"Error in generate_tts: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/tts/audio/<filename>', methods=['GET'])
def serve_tts_audio(filename):
    """
    Serve generated TTS audio files.

    Args:
        filename: Name of the audio file

    Returns:
        Audio file with proper mimetype and CORS headers
    """
    try:
        audio_path = settings.AUDIO_DIR / filename

        # Only audio this API generated; nothing else in the directory is public.
        if not TTS_FILENAME.fullmatch(filename) or not audio_path.exists():
            return jsonify({'success': False, 'error': 'Audio file not found'}), 404

        # Check if download is requested
        download = request.args.get('download', 'false').lower() == 'true'

        response = send_from_directory(
            settings.AUDIO_DIR,
            filename,
            mimetype='audio/mpeg',
            as_attachment=download,
            download_name='sanskrit_recitation.mp3' if download else None,
        )

        # Add explicit headers for better browser compatibility
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'no-cache'
        response.headers['Access-Control-Allow-Origin'] = '*'

        return response

    except Exception as e:
        logger.exception(f"Error serving TTS audio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@bp.route(f'{settings.API_PREFIX}/audio/transcribe', methods=['POST'])
def audio_transcribe():
    """
    Transcribe Sanskrit audio using IndicConformer ASR.

    Accepts audio files (WAV, MP3, WebM) and returns transcribed Sanskrit text.
    Uses AI4Bharat's IndicConformerASR model via external API.
    WebM files (from browser recording) are automatically converted to WAV.

    Request: Multipart form data with 'audio_file' field

    Returns:
        JSON with transcribed text
    """
    import subprocess

    import requests as http_requests

    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'webm', 'ogg', 'm4a', 'flac'}

    # Each upload gets a private directory that is removed on every exit path. Saving under the
    # client's filename in AUDIO_DIR let two "recording.wav" uploads overwrite each other, and
    # left recordings downloadable from /tts/audio/ whenever an early return skipped the cleanup.
    workdir = None
    try:
        # Handle multipart form data
        if 'audio_file' not in request.files:
            return jsonify({'success': False, 'error': 'No audio file provided'}), 400

        file = request.files['audio_file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Empty filename'}), 400

        if not allowed_file(file.filename, ALLOWED_AUDIO_EXTENSIONS):
            return jsonify({'success': False, 'error': f'Invalid file type. Allowed: {ALLOWED_AUDIO_EXTENSIONS}'}), 400

        filename = secure_filename(file.filename)
        workdir = Path(tempfile.mkdtemp(prefix='asr_'))
        filepath = workdir / filename
        file.save(filepath)

        logger.info(f"Audio transcription requested for: {filename}")

        # Check if we need to convert WebM to WAV (browser recordings are WebM/Opus)
        file_ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        audio_filepath = filepath
        converted_filepath = None

        if file_ext in ('webm', 'ogg', 'm4a'):
            # Convert to WAV using ffmpeg
            converted_filepath = workdir / 'converted.wav'
            logger.info(f"Converting {file_ext.upper()} to WAV: {converted_filepath}")

            try:
                # Use ffmpeg to convert to 16kHz mono WAV (optimal for ASR)
                result = subprocess.run(
                    [
                        'ffmpeg',
                        '-y',
                        '-i',
                        str(filepath),
                        '-ar',
                        '16000',  # 16kHz sample rate
                        '-ac',
                        '1',  # Mono
                        '-f',
                        'wav',
                        str(converted_filepath),
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode != 0:
                    logger.error(f"ffmpeg conversion failed: {result.stderr}")
                    return jsonify(
                        {
                            'success': False,
                            'error': 'Audio format conversion failed. Please upload a WAV or MP3 file.',
                        }
                    ), 400

                audio_filepath = converted_filepath

                # Get audio duration using ffprobe
                try:
                    probe_result = subprocess.run(
                        [
                            'ffprobe',
                            '-v',
                            'error',
                            '-show_entries',
                            'format=duration',
                            '-of',
                            'default=noprint_wrappers=1:nokey=1',
                            str(converted_filepath),
                        ],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )
                    duration = float(probe_result.stdout.strip()) if probe_result.stdout.strip() else 0
                    logger.info(f"Conversion successful: {converted_filepath} (duration: {duration:.2f}s)")

                    if duration < 1.0:
                        logger.warning(f"Audio too short: {duration:.2f}s")
                        return jsonify(
                            {
                                'success': False,
                                'error': 'Recording is too short. Please record at least 1 second of audio.',
                            }
                        ), 400
                except Exception as e:
                    logger.warning(f"Could not get audio duration: {e}")
                    logger.info(f"Conversion successful: {converted_filepath}")

            except FileNotFoundError:
                logger.error("ffmpeg not found. Cannot convert WebM to WAV.")
                return jsonify(
                    {
                        'success': False,
                        'error': 'Audio conversion not available. Please upload a WAV or MP3 file instead.',
                    }
                ), 400
            except subprocess.TimeoutExpired:
                logger.error("ffmpeg conversion timed out")
                return jsonify(
                    {'success': False, 'error': 'Audio conversion timed out. Please try a shorter recording.'}
                ), 400

        # Call IndicConformer ASR API
        asr_url = settings.INDIC_ASR_URL
        if not asr_url:
            logger.warning("INDIC_ASR_URL is not set; speech recognition is disabled")
            return jsonify({'success': False, 'error': 'Speech recognition is not configured on this server.'}), 503
        send_filename = audio_filepath.name

        try:
            with open(audio_filepath, 'rb') as audio_file:
                files = {'file': (send_filename, audio_file)}
                data = {'decoder': 'rnnt'}

                logger.info(f"Calling IndicConformer ASR at: {asr_url} with file: {send_filename}")
                response = http_requests.post(
                    asr_url,
                    files=files,
                    data=data,
                    timeout=120,  # 2 minute timeout for large audio files
                )

                if response.status_code != 200:
                    logger.error(f"ASR API returned status {response.status_code}: {response.text}")
                    return jsonify({'success': False, 'error': f'ASR service error: {response.status_code}'}), 502

                result = response.json()
                logger.info(f"ASR API response: {result}")

                # Extract transcription from response
                transcription = result.get('transcription', [])
                logger.info(f"Transcription field: {transcription}, type: {type(transcription)}")

                if isinstance(transcription, list) and len(transcription) > 0:
                    text = transcription[0].strip()
                elif isinstance(transcription, str):
                    text = transcription.strip()
                else:
                    text = ''

                if not text:
                    logger.warning("ASR returned empty transcription - audio may be silent or too short")
                    return jsonify(
                        {
                            'success': False,
                            'error': 'No speech detected in the audio. Please ensure you are speaking clearly into the microphone and try recording again.',
                        }
                    ), 400

                logger.info(f"ASR transcription complete: {len(text)} chars")

                return jsonify({'success': True, 'text': text, 'decoder_used': result.get('decoder_used', 'rnnt')})

        except http_requests.exceptions.Timeout:
            logger.error("ASR API request timed out")
            return jsonify(
                {'success': False, 'error': 'Audio transcription timed out. Please try a shorter audio file.'}
            ), 504
        except http_requests.exceptions.ConnectionError as e:
            logger.error(f"ASR API connection error: {e}")
            return jsonify(
                {'success': False, 'error': 'Could not connect to transcription service. Please try again later.'}
            ), 503

    except Exception as e:
        logger.exception(f"Error in audio_transcribe: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if workdir:
            shutil.rmtree(workdir, ignore_errors=True)
