"""
Request validation for the JSON API routes.

Handlers call ``parse_body(Model)`` with a model from backend.api.schemas
before their own try blocks. A failure raises RequestValidationError, which
app.py turns into a 400 response shaped like the routes' other errors:
{"success": false, "error": "<first problem>", "details": [{"field": ..., "message": ...}]}.
"""

from __future__ import annotations

from typing import TypeVar

from flask import jsonify, request
from pydantic import BaseModel, ValidationError

from backend.api.schemas import MAX_TEXT_LENGTH

__all__ = ["MAX_TEXT_LENGTH", "RequestValidationError", "handle_validation_error", "json_object", "parse_body"]

Model = TypeVar("Model", bound=BaseModel)


class RequestValidationError(ValueError):
    """The request body or a field in it is malformed."""

    def __init__(self, message: str, details: list[dict[str, str]] | None = None):
        super().__init__(message)
        self.details = details or []


def json_object() -> dict:
    """Return the request body as a dict, or raise if it is not a JSON object."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RequestValidationError("Request body must be a JSON object")
    return data


def describe(error: dict) -> str:
    """One readable sentence for a pydantic error, naming the field."""
    field = ".".join(str(part) for part in error["loc"]) or "body"
    kind, ctx = error["type"], error.get("ctx") or {}
    if kind == "missing":
        return f"Missing required field: {field}"
    if kind == "string_type":
        return f"'{field}' must be a string"
    if kind == "string_too_long":
        return f"'{field}' is longer than {ctx.get('max_length')} characters"
    if kind == "bool_type":
        return f"'{field}' must be true or false"
    if kind == "literal_error":
        return f"'{field}' must be one of {ctx.get('expected')}"
    if kind in ("dict_type", "model_type"):
        return f"'{field}' must be a JSON object"
    return f"'{field}': {error['msg']}"


def parse_body(model: type[Model], *, optional: bool = False) -> Model:
    """Validate the JSON body against `model` and return the parsed instance.

    With ``optional=True`` a request without a JSON body gets the model's defaults,
    for routes that accept a bare POST.
    """
    data = {} if optional and request.get_json(silent=True) is None else json_object()
    try:
        return model.model_validate(data)
    except ValidationError as exc:
        details = [{"field": ".".join(map(str, e["loc"])), "message": describe(e)} for e in exc.errors()]
        raise RequestValidationError(details[0]["message"], details) from None


def handle_validation_error(error: RequestValidationError):
    body = {"success": False, "error": str(error)}
    if error.details:
        body["details"] = error.details
    return jsonify(body), 400
