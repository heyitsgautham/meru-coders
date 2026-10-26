"""
REST API route registration.

Each feature area lives in its own module with a Blueprint:
identify, ocr_routes, datasets, verse_search and speech, plus the chatbot,
auth, contributions and community blueprints.
"""

from backend.config import settings


def register_routes(app):
    """Register every API blueprint on the Flask application."""
    from backend.api.chatbot import chatbot_bp
    from backend.api.community import community_bp
    from backend.api.datasets import bp as datasets_bp
    from backend.api.helpers import remove_request_uploads
    from backend.api.identify import bp as identify_bp
    from backend.api.ocr_routes import bp as ocr_bp
    from backend.api.speech import bp as speech_bp
    from backend.api.verse_search import bp as verse_search_bp
    from backend.auth.routes import auth_bp
    from backend.contributions.routes import contribution_bp

    app.teardown_request(remove_request_uploads)
    app.register_blueprint(chatbot_bp)
    app.register_blueprint(auth_bp, url_prefix=f'{settings.API_PREFIX}/auth')
    app.register_blueprint(contribution_bp, url_prefix=f'{settings.API_PREFIX}/contributions')
    app.register_blueprint(community_bp, url_prefix=f'{settings.API_PREFIX}/community')

    for blueprint in (identify_bp, ocr_bp, datasets_bp, verse_search_bp, speech_bp):
        app.register_blueprint(blueprint)
