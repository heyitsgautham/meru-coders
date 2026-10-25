"""Request bodies of the JSON API routes, declared as pydantic models.

Routes call ``parse_body(Model)`` from backend.api.validation before touching
the request. A body that does not fit its model never reaches the handler; the
client gets a 400 whose ``error`` names the first bad field and whose
``details`` lists every field problem.

Models describe types and bounds only. Rules that need the database or depend
on another field, such as a reserved username, stay in the handlers.
"""

from __future__ import annotations

from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StrictStr, StringConstraints

# Upper bound for pasted text. Whole files go through /identify/file instead.
MAX_TEXT_LENGTH = 50_000
MAX_NAME_LENGTH = 64
MAX_PASSWORD_LENGTH = 256

Text = Annotated[StrictStr, StringConstraints(max_length=MAX_TEXT_LENGTH)]
IdentificationMode = Literal["auto", "vedic", "classical", "dandaka"]


class RequestModel(BaseModel):
    """Base for request bodies: unknown fields are ignored, as the routes always did."""

    model_config = ConfigDict(extra="ignore")


class IdentifyTextRequest(RequestModel):
    text: Text
    output_scheme: StrictStr | None = None
    text_mode: Literal["line", "verse"] | None = None
    # The frontend once sent `mode`; it is still read when text_mode is absent.
    mode: Literal["line", "verse"] | None = None
    identification_mode: IdentificationMode = "auto"
    enable_sandhi: StrictBool = False

    @property
    def effective_text_mode(self) -> str:
        return self.text_mode or self.mode or "line"


class DandakaRequest(RequestModel):
    text: Text


class SlokaSearchRequest(RequestModel):
    text: Text
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    limit: int = Field(default=10, ge=1)


class SlokaValidateRequest(RequestModel):
    text: Text


class TTSRequest(RequestModel):
    text: Text
    voice: StrictStr = "male"


class ChatRequest(RequestModel):
    message: Text = ""
    conversation_id: StrictStr | None = None
    persona: StrictStr = "default"
    image: StrictStr | None = None
    audio: StrictStr | None = None


class AnalyzeMeterRequest(RequestModel):
    text: Text = ""
    conversation_id: StrictStr | None = None
    persona: StrictStr = "default"


class CredentialsRequest(RequestModel):
    """Signup, login and admin login. Missing or short values are the handlers' 400s."""

    username: StrictStr = Field(default="", max_length=MAX_NAME_LENGTH)
    password: StrictStr = Field(default="", max_length=MAX_PASSWORD_LENGTH)


class ContributionRequest(RequestModel):
    contribution_type: Literal["verse", "meter_definition"]
    data: dict[str, Any]


class ReviewRequest(RequestModel):
    review_notes: StrictStr = Field(default="", max_length=2_000)
