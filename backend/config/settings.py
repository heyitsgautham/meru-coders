"""
Application settings.

Every value that differs between machines comes from an environment
variable. Copy .env.example at the repository root to .env for local
development; python-dotenv loads it here without overriding variables already
set in the process environment. backend/.env is still read after it, for
checkouts set up before the file moved to the root.
"""

import os
import tempfile
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent
load_dotenv(REPO_ROOT / ".env")
load_dotenv(BACKEND_DIR / ".env")


def _env_int(name: str, default: int) -> int:
    """Read an integer environment variable, failing loudly on bad input."""
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


class Settings:
    """Application settings and configuration."""

    # Base paths
    BASE_DIR = BACKEND_DIR
    DATA_DIR = BASE_DIR / "data"
    UPLOADS_DIR = BASE_DIR / "uploads"
    PHOTOS_DIR = UPLOADS_DIR / "photos"
    TEXTS_DIR = UPLOADS_DIR / "texts"
    RESULTS_DIR = UPLOADS_DIR / "results"
    AUDIO_DIR = UPLOADS_DIR / "audio"
    TMP_PATH = Path(tempfile.gettempdir()) / "CHANDA_TMP"

    # Flask configuration
    APPLICATION_NAME = "Sanskrit Meter Identification System"
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key")
    DEBUG = _env_bool("DEBUG")
    MAX_CONTENT_LENGTH = _env_int("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)

    # API configuration
    API_PREFIX = "/api"

    # CORS configuration ("*" for development, restrict in production)
    CORS_ORIGINS = os.environ.get("CORS_ORIGINS", "*")

    # Supabase (auth, community and contributions). Optional for meter analysis.
    SUPABASE_URL = os.environ.get("SUPABASE_URL")
    SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

    # Rate limiting
    RATELIMIT_STORAGE_URL = os.environ.get("REDIS_URL", "memory://")
    RATELIMIT_DEFAULT = os.environ.get("RATELIMIT_DEFAULT", "100 per hour")
    RATELIMIT_AUTH = "5 per minute"

    # Logging
    LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
    # "text" for humans, "json" for log collectors
    LOG_FORMAT = os.environ.get("LOG_FORMAT", "text")

    # Error tracking: unset SENTRY_DSN keeps Sentry off
    SENTRY_DSN = os.environ.get("SENTRY_DSN", "")
    SENTRY_ENVIRONMENT = os.environ.get("SENTRY_ENVIRONMENT", "development")
    SENTRY_TRACES_SAMPLE_RATE = float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE", "0"))

    # OCR configuration
    TESSERACT_LANGUAGES = ["san", "hin", "eng"]
    # Service account JSON for Google Cloud Vision OCR and Cloud TTS
    GCP_CREDENTIALS = os.environ.get(
        "GOOGLE_APPLICATION_CREDENTIALS",
        str(BASE_DIR / "secrets" / "gcp-credentials.json"),
    )

    # Chanda configuration: "auto" (ICU when available), "icu" or "sanskrit_text"
    SYLLABIZATION_METHOD = os.environ.get("SYLLABIZATION_METHOD", "auto")

    # File upload restrictions
    ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff"}
    ALLOWED_TEXT_EXTENSIONS = {"txt", "text"}
    ALLOWED_DOCUMENT_EXTENSIONS = {"docx", "txt", "text"}
    ALLOWED_AUDIO_EXTENSIONS = {"wav", "mp3", "webm", "ogg", "m4a", "flac"}
    MAX_FILE_SIZE_MB = 10

    # IndicConformer speech recognition service. Voice input is disabled when unset.
    INDIC_ASR_URL = os.environ.get("INDIC_ASR_URL", "")

    # Upload cleanup: how often the job runs and how old a file must be to go
    # The test suite turns the background cleanup job off; see backend/tests/conftest.py.
    CLEANUP_ENABLED = _env_bool("CLEANUP_ENABLED", True)
    CLEANUP_INTERVAL_MINUTES = _env_int("CLEANUP_INTERVAL_MINUTES", 60)
    FILE_MAX_AGE_MINUTES = _env_int("FILE_MAX_AGE_MINUTES", 60)

    def __init__(self):
        """Create the upload and temp directories the API writes into."""
        for directory in [
            self.UPLOADS_DIR,
            self.PHOTOS_DIR,
            self.TEXTS_DIR,
            self.RESULTS_DIR,
            self.AUDIO_DIR,
            self.TMP_PATH,
        ]:
            directory.mkdir(parents=True, exist_ok=True)


# Legacy module-level names kept for scripts that import them directly
BASE_DIR = Settings.BASE_DIR
DATA_PATH = Settings.DATA_DIR
TMP_PATH = Settings.TMP_PATH
APPLICATION_NAME = Settings.APPLICATION_NAME
SECRET_KEY = Settings.SECRET_KEY
GCP_CREDENTIALS = Settings.GCP_CREDENTIALS

settings = Settings()
