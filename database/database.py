"""Deprecated compatibility exports for the unified async database layer.

New code must import these objects from :mod:`app.database` directly.
"""

from app.database import Base, async_session_maker, engine, get_db, init_db

__all__ = ["Base", "async_session_maker", "engine", "get_db", "init_db"]
