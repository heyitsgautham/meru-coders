"""Endpoint tests for the blueprints split out of api/routes.py."""

import io

import pytest

from backend.api import datasets, helpers, verse_search
from backend.config import settings

GITA_LINE = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"


@pytest.mark.parametrize(
    ("filename", "allowed"),
    [("verse.txt", True), ("verse.PDF", True), ("verse.docx", True), ("verse.exe", False), ("no_extension", False)],
)
def test_allowed_file(filename, allowed):
    assert helpers.allowed_file(filename, helpers.ALLOWED_DOCUMENT_EXTENSIONS) is allowed


class TestDatasets:
    def test_catalog_lists_every_dataset(self, client):
        catalog = datasets.load_dataset_catalog()
        resp = client.get("/api/datasets")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert len(body["datasets"]) == len(catalog["datasets"])

    def test_dataset_rows_are_paginated(self, client):
        dataset_id = next(
            ds_id for ds_id, ds in datasets.load_dataset_catalog()["datasets"].items() if "files" not in ds
        )
        first = client.get(f"/api/datasets/{dataset_id}?limit=3&offset=0").get_json()
        second = client.get(f"/api/datasets/{dataset_id}?limit=3&offset=3").get_json()
        assert first["success"] is True
        assert len(first["rows"]) == 3
        assert first["rows"] != second["rows"]

    def test_unknown_dataset_is_404(self, client):
        resp = client.get("/api/datasets/not-a-dataset")
        assert resp.status_code == 404

    def test_examples_and_schemes(self, client):
        examples = client.get("/api/examples").get_json()
        schemes = client.get("/api/schemes").get_json()
        assert examples["success"] is True and examples["examples"]
        assert {"devanagari", "iast", "slp1"} <= {scheme["value"] for scheme in schemes["schemes"]}


class TestIdentify:
    def test_dandaka_mode_classifies_units(self, client):
        resp = client.post("/api/identify/dandaka", json={"text": "रामो राजमणिः सदा विजयते । रामं रमेशं भजे ॥"})
        assert resp.status_code == 200
        result = resp.get_json()["result"]
        assert result["mode"] == "dandaka"
        assert len(result["dandaka"]["units"]) == 2

    def test_dandaka_requires_text(self, client):
        assert client.post("/api/identify/dandaka", json={}).status_code == 400

    def test_text_file_upload_is_identified(self, client):
        data = {"text_file": (io.BytesIO(GITA_LINE.encode("utf-8")), "gita.txt")}
        resp = client.post("/api/identify/file", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        body = resp.get_json()
        assert body["success"] is True
        assert body["result"]["line"][0]["result"]["found"] is True

    def test_disallowed_extension_is_rejected(self, client):
        data = {"text_file": (io.BytesIO(b"MZ"), "virus.exe")}
        resp = client.post("/api/identify/file", data=data, content_type="multipart/form-data")
        assert resp.status_code == 400

    def test_download_missing_file_is_404(self, client):
        assert client.get("/api/download/does-not-exist.json").status_code == 404

    def test_download_cannot_escape_results_dir(self, client):
        assert client.get("/api/download/..%2F..%2Fconfig%2Fsettings.py").status_code == 404

    def test_download_serves_a_result_file(self, client):
        path = settings.RESULTS_DIR / "pytest-result.txt"
        path.write_text("ok", encoding="utf-8")
        try:
            resp = client.get("/api/download/pytest-result.txt")
            assert resp.status_code == 200
            assert resp.data == b"ok"
        finally:
            path.unlink()


class TestVerseSearch:
    def test_cache_lookup_finds_known_verse(self):
        match = verse_search.find_cached_verse_match("अग्निमीळे पुरोहितं यज्ञस्य देवमृत्विजं होतारं रत्नधातमं")
        assert match["found"] is True
        assert match["similarity"] >= verse_search.CACHE_EXACT_MATCH_THRESHOLD

    def test_cache_lookup_misses_unknown_text(self):
        assert verse_search.find_cached_verse_match("कखगघ")["found"] is False

    def test_validate_requires_text(self, client):
        assert client.post("/api/sloka/validate", json={}).status_code == 400


class TestSpeech:
    def test_tts_requires_text(self, client):
        resp = client.post("/api/tts/generate", json={})
        assert resp.status_code == 400
        assert resp.get_json()["error"] == "Missing required field: text"

    def test_transcribe_requires_a_file(self, client):
        assert client.post("/api/audio/transcribe").status_code == 400

    def test_missing_audio_is_404(self, client):
        assert client.get("/api/tts/audio/missing.mp3").status_code == 404


class TestOcrRoutes:
    def test_ocr_extract_requires_a_file(self, client):
        assert client.post("/api/ocr/extract").status_code == 400

    def test_file_extract_returns_text(self, client):
        data = {"file": (io.BytesIO(GITA_LINE.encode("utf-8")), "gita.txt")}
        resp = client.post("/api/file/extract", data=data, content_type="multipart/form-data")
        assert resp.status_code == 200
        assert GITA_LINE in resp.get_json()["text"]
