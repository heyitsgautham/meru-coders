"""Upload helpers shared by the API route modules."""

import shutil
import tempfile
from pathlib import Path

from flask import g

# Verse corpora behind the dataset browser and verse search
SOURCE_DIR = Path(__file__).parent.parent / 'source'

# Extended allowed extensions for multi-format support
ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'docx', 'txt', 'text'}


def allowed_file(filename, allowed_extensions):
    """Check if file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def request_upload_path(filename: str) -> Path:
    """Where to save this request's upload: a private directory removed when the request ends.

    Uploads used to land in uploads/photos, uploads/texts and uploads/audio under the client's
    filename. Concurrent uploads of the same name overwrote each other, and public routes served
    whatever an early return had left behind.
    """
    workdir = Path(tempfile.mkdtemp(prefix='upload_'))
    g.setdefault('upload_dirs', []).append(workdir)
    return workdir / filename


def remove_request_uploads(_exc=None):
    """Teardown hook: delete the directories request_upload_path created for this request."""
    for workdir in g.pop('upload_dirs', []):
        shutil.rmtree(workdir, ignore_errors=True)
