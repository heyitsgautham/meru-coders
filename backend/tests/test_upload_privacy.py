"""Uploaded documents and images live only for their request and are never served back."""

import io
import tempfile
from pathlib import Path

import pytest

from backend.config import settings

TEXT = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः।\nमामकाः पाण्डवाश्चैव किमकुर्वत सञ्जय॥\n".encode()


@pytest.fixture
def uploads(tmp_path, monkeypatch):
    """Point every upload directory at an empty tree, and record what the requests leave behind."""
    root = tmp_path / "uploads"
    for name, sub in [("UPLOADS_DIR", ""), ("PHOTOS_DIR", "photos"), ("TEXTS_DIR", "texts"), ("AUDIO_DIR", "audio")]:
        path = root / sub
        path.mkdir(parents=True, exist_ok=True)
        monkeypatch.setattr(settings, name, path)
    temp_root = tmp_path / "tmp"
    temp_root.mkdir()
    monkeypatch.setattr(tempfile, "tempdir", str(temp_root))
    return root, temp_root


def _files(root: Path):
    return sorted(str(p.relative_to(root)) for p in root.rglob("*") if p.is_file())


def test_an_extracted_document_is_deleted_after_its_request(client, uploads):
    root, temp_root = uploads

    resp = client.post(
        "/api/file/extract",
        data={"file": (io.BytesIO(TEXT), "notes.txt")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert resp.get_json()["file_info"]["filename"] == "notes.txt"
    assert _files(root) == []
    assert _files(temp_root) == []


def test_identifying_a_file_leaves_no_copy(client, uploads):
    root, temp_root = uploads

    resp = client.post(
        "/api/identify/file",
        data={"text_file": (io.BytesIO(TEXT), "gita.txt")},
        content_type="multipart/form-data",
    )

    assert resp.status_code == 200
    assert [f for f in _files(root) if not f.startswith("results/")] == []
    assert _files(temp_root) == []


@pytest.mark.parametrize("path", ["texts/notes.txt", "photos/page.png", "audio/recording.wav", "results/r.json"])
def test_the_community_file_route_serves_only_post_images(client, uploads, path):
    root, _ = uploads
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(b"private")

    assert client.get(f"/api/community/uploads/{path}").status_code == 404


def test_post_images_are_still_served(client, uploads):
    root, _ = uploads
    image = root / "community" / "u1" / "a.png"
    image.parent.mkdir(parents=True)
    image.write_bytes(b"\x89PNG")

    resp = client.get("/api/community/uploads/community/u1/a.png")

    assert resp.status_code == 200
    assert resp.data == b"\x89PNG"
