"""
CliqUp Backend Entry Point
==========================

This file serves as the entry point for the backend application.
It imports and exposes the FastAPI app from the modular architecture.

The actual implementation is in:
- app.py: Main application setup
- core/: Configuration, database, security
- modules/: Domain modules (identity, profiles, social, meet, messaging)
- utils/: Helper functions and algorithms
"""
from app import app

# Re-export the app for uvicorn
__all__ = ["app"]
