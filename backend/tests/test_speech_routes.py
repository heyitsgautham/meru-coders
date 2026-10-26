"""Text-to-speech and transcription routes, with every engine and the ASR service faked."""

import io
import types
from unittest.mock import MagicMock

import pytest
import requests

from backend.api import speech
from backend.config import settings

WAV = b"RIFF" + b"\0" * 40


@pytest.fixture
def audio_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "AUDIO_DIR", tmp_path / "audio")
    settings.AUDIO_DIR.mkdir()
    return settings.AUDIO_DIR


@pytest.fixture
def client(app, audio_dir):
    with app.test_client() as test_client:
        yield test_client


def _upload(client, name="recording.wav", data=WAV):
    return client.post(
        "/api/audio/transcribe",
        data={"audio_file": (io.BytesIO(data), name)},
        content_type="multipart/form-data",
    )


class TestTranscribe:
    def test_a_recording_is_never_left_where_the_audio_route_serves_it(self, client, audio_dir, monkeypatch):
        monkeypatch.setattr(settings, "INDIC_ASR_URL", "")

        resp = _upload(client)

        assert resp.status_code == 503
        assert list(audio_dir.iterdir()) == []
        assert client.get("/api/tts/audio/recording.wav").status_code == 404

    def test_sends_the_audio_to_the_asr_service_and_returns_its_text(self, client, audio_dir, monkeypatch):
        monkeypatch.setattr(settings, "INDIC_ASR_URL", "http://asr.test/transcribe")
        seen = {}

        def post(url, files, data, timeout):
            seen["url"], seen["bytes"], seen["decoder"] = url, files["file"][1].read(), data["decoder"]
            return MagicMock(status_code=200, json=lambda: {"transcription": [" धर्मक्षेत्रे "], "decoder_used": "rnnt"})

        monkeypatch.setattr(requests, "post", post)

        resp = _upload(client)

        assert resp.get_json() == {"success": True, "text": "धर्मक्षेत्रे", "decoder_used": "rnnt"}
        assert seen == {"url": "http://asr.test/transcribe", "bytes": WAV, "decoder": "rnnt"}
        assert list(audio_dir.iterdir()) == []

    @pytest.mark.parametrize(
        ("reply", "status", "message"),
        [
            (MagicMock(status_code=500, text="boom"), 502, "ASR service error: 500"),
            (MagicMock(status_code=200, json=lambda: {"transcription": []}), 400, "No speech detected"),
            (requests.exceptions.Timeout(), 504, "timed out"),
            (requests.exceptions.ConnectionError(), 503, "Could not connect"),
        ],
    )
    def test_reports_asr_failures(self, client, monkeypatch, reply, status, message):
        monkeypatch.setattr(settings, "INDIC_ASR_URL", "http://asr.test/transcribe")

        def post(*_args, **_kwargs):
            if isinstance(reply, Exception):
                raise reply
            return reply

        monkeypatch.setattr(requests, "post", post)

        resp = _upload(client)

        assert resp.status_code == status
        assert message in resp.get_json()["error"]

    @pytest.mark.parametrize(("name", "error"), [(None, "No audio file provided"), ("notes.txt", "Invalid file type")])
    def test_rejects_missing_or_foreign_files(self, client, name, error):
        resp = client.post("/api/audio/transcribe") if name is None else _upload(client, name)
        assert resp.status_code == 400
        assert error in resp.get_json()["error"]


class TestTts:
    @pytest.fixture
    def engines(self, monkeypatch):
        """edge-tts and gTTS stand-ins; Google Cloud TTS is switched off."""
        calls = []

        class Communicate:
            def __init__(self, text, voice):
                calls.append(("edge", text, voice))

            async def save(self, path):
                if engines_state["edge_fails"]:
                    raise RuntimeError("edge offline")
                with open(path, "wb") as out:
                    out.write(b"ID3edge")

        class GTTS:
            def __init__(self, text, lang, slow):
                calls.append(("gtts", text, lang))

            def save(self, path):
                with open(path, "wb") as out:
                    out.write(b"ID3gtts")

        engines_state = {"edge_fails": False}
        monkeypatch.setattr(speech, "GOOGLE_TTS_AVAILABLE", False)
        monkeypatch.setattr(speech, "EDGE_TTS_AVAILABLE", True)
        monkeypatch.setattr(speech, "GTTS_AVAILABLE", True)
        monkeypatch.setattr(speech, "edge_tts", types.SimpleNamespace(Communicate=Communicate), raising=False)
        monkeypatch.setattr(speech, "gTTS", GTTS, raising=False)
        return calls, engines_state

    def test_generates_with_edge_tts_and_serves_the_file(self, client, engines):
        calls, _ = engines

        body = client.post("/api/tts/generate", json={"text": " रामो राजमणिः ", "voice": "female"}).get_json()

        assert body["success"] is True and body["engine"] == "edge-tts"
        assert calls == [("edge", "रामो राजमणिः", "hi-IN-SwaraNeural")]
        audio = client.get(body["audio_url"])
        assert audio.status_code == 200
        assert audio.data == b"ID3edge"
        assert audio.headers["Content-Type"] == "audio/mpeg"
        download = client.get(f"{body['audio_url']}?download=true")
        assert "sanskrit_recitation.mp3" in download.headers["Content-Disposition"]

    def test_falls_back_to_gtts_when_edge_tts_fails(self, client, engines, audio_dir):
        calls, state = engines
        state["edge_fails"] = True

        body = client.post("/api/tts/generate", json={"text": "नमः"}).get_json()

        assert body["success"] is True
        assert body["engine"].startswith("gTTS")
        assert [call[0] for call in calls] == ["edge", "gtts"]
        assert [path.name for path in audio_dir.iterdir()] == [body["filename"]]

    def test_rejects_empty_text(self, client, engines):
        resp = client.post("/api/tts/generate", json={"text": "   "})
        assert resp.status_code == 400

    def test_says_when_no_engine_is_installed(self, client, monkeypatch):
        for flag in ("GOOGLE_TTS_AVAILABLE", "EDGE_TTS_AVAILABLE", "GTTS_AVAILABLE", "PYTTSX3_AVAILABLE"):
            monkeypatch.setattr(speech, flag, False)
        assert client.post("/api/tts/generate", json={"text": "नमः"}).status_code == 503


def test_the_audio_route_serves_only_generated_files(client, audio_dir):
    (audio_dir / "notes.mp3").write_bytes(b"private")
    assert client.get("/api/tts/audio/notes.mp3").status_code == 404
    assert client.get(f"/api/tts/audio/tts_{'0' * 32}.mp3").status_code == 404
