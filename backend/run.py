#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Backend API Server

Entry point for the Flask REST API backend.
"""

import sys
from pathlib import Path

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.app import create_app


def main():
    """Start the Flask REST API server."""
    app = create_app()
    
    print("=" * 70)
    print("🚀 Sanskrit Meter Identification - REST API Backend")
    print("=" * 70)
    print("📍 API Endpoint: http://localhost:5000/api")
    print("📍 Health Check: http://localhost:5000/health")
    print("📍 API Info:     http://localhost:5000/api/info")
    print("=" * 70)
    print("💡 Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    # Run the Flask app
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True,
        threaded=True
    )


if __name__ == '__main__':
    main()
