"""Upload helpers shared by the API route modules."""

from pathlib import Path

# Verse corpora behind the dataset browser and verse search
SOURCE_DIR = Path(__file__).parent.parent / 'source'

# Extended allowed extensions for multi-format support
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'txt', 'text'}


def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions
