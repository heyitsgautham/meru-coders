#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API Server

Entry point for the Flask REST API backend.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app


def main():
    """Start the Flask REST API server."""
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
    print("=" * 70)
    print("💡 Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG'],
        threaded=True
    )


if __name__ == '__main__':
    main()
