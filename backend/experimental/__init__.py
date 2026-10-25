"""Alternative engines and models that the evaluation harnesses compare against the served engine.

Nothing here is imported by the API. EnhancedChanda applies Chandovallari rules,
ChandaModal adds an explicit Vedic or classical mode, ChandaHybrid syllabifies
with ICU, and SanskritTTS wraps a local Parler-TTS model. The engine the app
serves is backend.core.chanda.Chanda.
"""
