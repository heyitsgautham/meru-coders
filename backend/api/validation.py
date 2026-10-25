"""
Request validation for the JSON API routes.

Handlers call these helpers before their own try blocks. A failure raises
RequestValidationError, which app.py turns into a 400 response shaped like
the routes' other errors: {"success": false, "error": "<message>"}.
"""

from flask import jsonify, request

# Upper bound for pasted text. Whole files go through /identify/file instead.
MAX_TEXT_LENGTH = 50_000


class RequestValidationError(ValueError):
    """The request body or a field in it is malformed."""


def json_object():
    """Return the request body as a dict, or raise if it is not a JSON object."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise RequestValidationError("Request body must be a JSON object")
    return data


def optional_string(data, field, max_length=MAX_TEXT_LENGTH):
    """Return data[field] when it is a string within max_length, or None when absent."""
    value = data.get(field)
    if value is None:
        return None
    if not isinstance(value, str):
        raise RequestValidationError(f"'{field}' must be a string")
    if len(value) > max_length:
        raise RequestValidationError(f"'{field}' is longer than {max_length} characters")
    return value


def text_payload(field="text", max_length=MAX_TEXT_LENGTH):
    """Validate a JSON object body whose `field` is an optional string; return the body."""
    data = json_object()
    optional_string(data, field, max_length)
    return data


def handle_validation_error(error):
    return jsonify({"success": False, "error": str(error)}), 400
