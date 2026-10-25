"""POST /api/chatbot/chat end to end, with Gemini, RAG, OCR and speech replaced by fakes.

The route reads its collaborators from several modules; ``patch_everywhere``
replaces a name in each module that defines it, so these tests do not depend
on which module the chat code imports it from.
"""

import base64
import sys
import types as pytypes

import pytest

from backend.api import chatbot, chatbot_ai

GITA = "धर्मक्षेत्रे कुरुक्षेत्रे समवेता युयुत्सवः"


def chat_modules():
    names = ["backend.api.chatbot", "backend.api.chatbot_ai", "backend.api.chatbot_media"]
    return [sys.modules[name] for name in names if name in sys.modules]


def patch_everywhere(monkeypatch, name, value):
    for module in chat_modules():
        if hasattr(module, name):
            monkeypatch.setattr(module, name, value)


class FakeChat:
    def __init__(self, replies):
        self.replies = replies
        self.sent = []

    def send_message(self, message):
        self.sent.append(message)
        reply = self.replies.pop(0)
        if isinstance(reply, Exception):
            raise reply
        return pytypes.SimpleNamespace(text=reply)


class FakeGemini:
    """Stands in for get_gemini_client; every client shares one scripted list of replies."""

    def __init__(self, *replies):
        self.chat = FakeChat(list(replies))
        self.clients = []
        self.histories = []

    def __call__(self, exclude_keys=None):
        if exclude_keys and len(exclude_keys) >= 2:
            raise ValueError("all keys exhausted")
        client = pytypes.SimpleNamespace(api_key=f"key-{len(self.clients)}")
        client.chats = pytypes.SimpleNamespace(create=self._create)
        self.clients.append(client)
        return client

    def _create(self, model, config, history):
        self.histories.append(history)
        return self.chat


@pytest.fixture
def chat_client(app, monkeypatch):
    monkeypatch.setattr(chatbot, "conversations", {})
    patch_everywhere(monkeypatch, "get_rag_engine", lambda: None)
    patch_everywhere(monkeypatch, "GEMINI_API_KEYS", ["key-a", "key-b"])
    with app.test_client() as client:
        yield client


def post(client, **body):
    resp = client.post("/api/chatbot/chat", json=body)
    return resp.status_code, resp.get_json()


def test_plain_question_gets_the_gemini_reply_and_is_remembered(chat_client, monkeypatch):
    gemini = FakeGemini("Anuṣṭubh has eight syllables per pada.")
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)

    status, body = post(chat_client, message="How long is an Anushtubh pada?", conversation_id="c1")

    assert status == 200
    assert body["response"] == "Anuṣṭubh has eight syllables per pada."
    assert (body["response_source"], body["rag_docs_used"]) == ("ai", 0)
    assert [m["role"] for m in chatbot.conversations["c1"]] == ["user", "assistant"]
    assert gemini.chat.sent == ["How long is an Anushtubh pada?"]


def test_history_carries_earlier_turns(chat_client, monkeypatch):
    gemini = FakeGemini("first", "second")
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)
    post(chat_client, message="one", conversation_id="c2")
    post(chat_client, message="two", conversation_id="c2")
    assert [content.role for content in gemini.histories[1]] == ["user", "model"]


def test_unknown_persona_is_rejected(chat_client):
    status, body = post(chat_client, message="hi", persona="nobody")
    assert status == 400
    assert body["error"].startswith("Invalid persona")


def test_meter_questions_are_answered_by_the_engine_not_gemini(chat_client, monkeypatch):
    gemini = FakeGemini()
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)

    status, body = post(chat_client, message=f"What is the chanda of {GITA}?", conversation_id="m1")

    assert status == 200
    assert body["agentic_action"] == "meter_identification"
    assert body["meter_data"]["found"]
    assert gemini.clients == []
    assert chatbot.conversations["m1"][0]["meter_intent_detected"] is True


def test_quota_errors_rotate_to_the_next_key(chat_client, monkeypatch):
    gemini = FakeGemini(RuntimeError("429 RESOURCE_EXHAUSTED"), "answer from the second key")
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)
    status, body = post(chat_client, message="hello")
    assert status == 200
    assert body["response"] == "answer from the second key"
    assert len(gemini.clients) == 2


def test_quota_on_every_key_is_a_429(chat_client, monkeypatch):
    gemini = FakeGemini(RuntimeError("quota exceeded"), RuntimeError("quota exceeded"))
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)
    status, body = post(chat_client, message="hello")
    assert status == 429
    assert body["error"] == "Service is temporarily busy. Please wait a moment and try again."


@pytest.mark.parametrize(
    ("error", "status", "message"),
    [
        ("finish_reason is 2", 400, "Content was blocked by safety filters. Please rephrase your question."),
        ("RECITATION", 400, "Content blocked due to recitation policy."),
        ("boom", 500, "Error processing request: boom"),
    ],
)
def test_gemini_failures_map_to_messages(chat_client, monkeypatch, error, status, message):
    patch_everywhere(monkeypatch, "get_gemini_client", FakeGemini(RuntimeError(error)))
    assert post(chat_client, message="hello") == (status, {"success": False, "error": message})


def test_rag_context_is_prepended_when_documents_match(chat_client, monkeypatch):
    class Engine:
        def is_ready(self):
            return True

        def retrieve(self, query, k, min_score):
            return [pytypes.SimpleNamespace(metadata={"source": "chandovallari"})] * 2

        def format_context_for_prompt(self, documents, include_source, max_length):
            return "Indravajrā has eleven syllables."

    gemini = FakeGemini("grounded answer")
    patch_everywhere(monkeypatch, "get_rag_engine", Engine)
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)

    status, body = post(chat_client, message="Tell me about Indravajra")

    assert status == 200
    assert (body["response_source"], body["rag_docs_used"]) == ("rag", 2)
    assert gemini.chat.sent[0].startswith("Context from knowledge base")
    assert "User question: Tell me about Indravajra" in gemini.chat.sent[0]


def png_data_url(payload=b"x" * 200):
    return "data:image/png;base64," + base64.b64encode(payload).decode()


def test_tiny_images_are_rejected(chat_client):
    status, body = post(chat_client, message="", image=png_data_url(b"x" * 10))
    assert status == 400
    assert body["error"].startswith("Image data appears to be invalid")


def test_image_text_is_read_by_cloud_vision_and_analysed(app, chat_client, monkeypatch):
    app.cloud_vision_ocr = pytypes.SimpleNamespace(extract_text_from_bytes=lambda data: f"  {GITA}  ")
    patch_everywhere(monkeypatch, "get_gemini_client", FakeGemini())

    status, body = post(chat_client, message="", image=png_data_url(), conversation_id="i1")

    assert status == 200
    assert body["agentic_action"] == "meter_identification"
    assert chatbot.conversations["i1"][0]["ocr_text"] == GITA


def test_an_image_without_text_is_a_400(app, chat_client):
    app.cloud_vision_ocr = pytypes.SimpleNamespace(extract_text_from_bytes=lambda data: "   ")
    status, body = post(chat_client, message="", image=png_data_url())
    assert status == 400
    assert body["error"].startswith("Could not extract any text from the image")


def test_without_an_ocr_service_images_fail(app, chat_client):
    app.cloud_vision_ocr = None
    app.tesseract_ocr = None
    status, body = post(chat_client, message="", image=png_data_url())
    assert (status, body["error"]) == (500, "OCR service is not available. Please contact support.")


def test_audio_without_speech_support_is_a_500(chat_client, monkeypatch):
    patch_everywhere(monkeypatch, "SPEECH_AVAILABLE", False)
    status, body = post(chat_client, message="", audio="data:audio/webm;base64,AAAA")
    assert status == 500
    assert body["error"].startswith("Audio transcription service is not available")


class FakeSpeech:
    """Minimal google.cloud.speech_v1 stand-in that hears a fixed transcript."""

    def __init__(self, transcript):
        self.transcript = transcript
        enc = pytypes.SimpleNamespace(WEBM_OPUS="webm", ENCODING_UNSPECIFIED="auto")
        self.RecognitionConfig = type("RecognitionConfig", (), {"AudioEncoding": enc, "__init__": lambda s, **kw: None})
        self.RecognitionAudio = lambda content: content
        outer = self

        class Client:
            def recognize(self, config, audio):
                alternative = pytypes.SimpleNamespace(transcript=outer.transcript)
                result = pytypes.SimpleNamespace(alternatives=[alternative], language_code="sa-IN")
                return pytypes.SimpleNamespace(results=[result] if outer.transcript else [])

        self.SpeechClient = Client


def test_audio_is_transcribed_into_the_message(chat_client, monkeypatch):
    gemini = FakeGemini("reply")
    patch_everywhere(monkeypatch, "SPEECH_AVAILABLE", True)
    patch_everywhere(monkeypatch, "gcp_speech", FakeSpeech("om namah shivaya"))
    patch_everywhere(monkeypatch, "get_gemini_client", gemini)

    status, _body = post(chat_client, message="Explain", audio="data:audio/webm;base64,AAAA", conversation_id="a1")

    assert status == 200
    assert chatbot.conversations["a1"][0]["content"] == "Explain\n\n[Transcribed from audio]: om namah shivaya"
    assert chatbot.conversations["a1"][0]["has_audio"] is True


def test_silent_audio_is_a_400(chat_client, monkeypatch):
    patch_everywhere(monkeypatch, "SPEECH_AVAILABLE", True)
    patch_everywhere(monkeypatch, "gcp_speech", FakeSpeech(""))
    status, body = post(chat_client, message="", audio="data:audio/webm;base64,AAAA")
    assert status == 400
    assert body["error"].startswith("Could not understand the audio")


def test_chatbot_ai_keys_are_patched_in_tests(chat_client):
    assert chatbot_ai.GEMINI_API_KEYS == ["key-a", "key-b"]
