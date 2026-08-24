"""Deprecated entry point kept for teammates using the earlier demo command.

Run ``uvicorn app.main:app`` for new development.
"""

from app.main import app

__all__ = ["app"]
