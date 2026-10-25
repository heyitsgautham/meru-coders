"""One shared Chanda engine per process.

Building a Chanda loads every meter CSV, which takes about 60 ms; identifying a
line takes about 2 ms. Routes and helpers call ``get_engine()`` instead of
constructing their own engine per request.
"""

from __future__ import annotations

from functools import lru_cache

from flask import current_app, has_app_context

from backend.config import settings

from .chanda import Chanda


@lru_cache(maxsize=1)
def _standalone_engine() -> Chanda:
    return Chanda(data_path=str(settings.DATA_DIR), syllabization_method=settings.SYLLABIZATION_METHOD)


def get_engine() -> Chanda:
    """The app's engine inside a Flask app context, else one engine cached for the process."""
    if has_app_context():
        engine = getattr(current_app, "chanda", None)
        if engine is not None:
            return engine
    return _standalone_engine()
