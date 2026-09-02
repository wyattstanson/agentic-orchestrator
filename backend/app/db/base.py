"""Database engine + session.

SQLite by default (offline, zero-setup). Point DATABASE_URL at Supabase's
Postgres connection string to use Supabase — no code change.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


@lru_cache
def get_engine():
    url = get_settings().resolved_database_url
    is_sqlite = url.startswith("sqlite")
    connect_args = {"check_same_thread": False, "timeout": 30} if is_sqlite else {}
    engine = create_engine(
        url, connect_args=connect_args, pool_pre_ping=True, future=True
    )

    if is_sqlite:
        # WAL + a busy timeout so the orchestrator's worker threads can write
        # concurrently without "database is locked".
        @event.listens_for(engine, "connect")
        def _sqlite_pragmas(dbapi_conn, _record):  # noqa: ANN001
            cur = dbapi_conn.cursor()
            cur.execute("PRAGMA journal_mode=WAL")
            cur.execute("PRAGMA busy_timeout=30000")
            cur.close()

    # Register models and create tables (idempotent).
    from . import models  # noqa: F401

    Base.metadata.create_all(engine)
    return engine


@lru_cache
def get_sessionmaker():
    return sessionmaker(bind=get_engine(), expire_on_commit=False, class_=Session)


def session() -> Session:
    return get_sessionmaker()()


def init_db() -> None:
    """Ensure the engine + tables exist. Safe to call repeatedly."""
    get_engine()
