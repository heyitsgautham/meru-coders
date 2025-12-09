#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API Server

Entry point for the Flask REST API backend with WebSocket support.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app, socketio


def main():
    """Start the Flask REST API server with WebSocket support."""
    app = create_app()
    
    # Get port from environment variable (Cloud Run) or default to 5000 (local dev)
    port = int(os.environ.get('PORT', 5000))
    
    print("=" * 70)
    print("🚀 Chandas-Integrated - Sanskrit Meter Identification System")
    print("=" * 70)
    print(f"📍 API Endpoint: http://localhost:{port}/api")
    print(f"📍 Health Check: http://localhost:{port}/health")
    print(f"📍 API Info:     http://localhost:{port}/api/info")
    print(f"📍 Examples:     http://localhost:{port}/api/examples")
    if socketio:
        print(f"📍 WebSocket:    http://localhost:{port}/socket.io")
    print("=" * 70)
    print("💡 Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    # Run with SocketIO if available, otherwise fall back to Flask
    if socketio:
        print("🔌 Running with WebSocket support (Flask-SocketIO threading mode)")
        socketio.run(
            app,
            host='0.0.0.0',
            port=port,
            debug=app.config['DEBUG'],
            allow_unsafe_werkzeug=True,  # Required for threading mode
            use_reloader=False  # Disable reloader to preserve Python path for RAG
        )
    else:
        print("⚠️ WebSocket not available, running standard Flask server")
        app.run(
            host='0.0.0.0',
            port=port,
            debug=app.config['DEBUG'],
            threaded=True,
            use_reloader=False  # Disable reloader to preserve Python path for RAG
        )


if __name__ == '__main__':
    main()
