"""PostgreSQL engine and session-factory helpers for HazeGuard."""

from __future__ import annotations

import os
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


class DatabaseConfigurationError(ValueError):
    """Raised when the database connection URL is not configured."""


def database_url_from_environment() -> str:
    """Return the database URL without exposing it through logs or errors."""
    database_url = os.getenv("HAZEGUARD_DATABASE_URL")
    if not database_url:
        raise DatabaseConfigurationError("HAZEGUARD_DATABASE_URL must be configured")
    return database_url


def create_database_engine(database_url: str | None = None) -> Engine:
    """Create a PostgreSQL SQLAlchemy engine with stale-connection checks."""
    return create_engine(database_url or database_url_from_environment(), pool_pre_ping=True)


def create_session_factory(database_url: str | None = None) -> sessionmaker[Session]:
    """Create independent sessions for repository operations."""
    return sessionmaker(bind=create_database_engine(database_url), expire_on_commit=False)


@contextmanager
def session_scope(session_factory: sessionmaker[Session]) -> Iterator[Session]:
    """Commit a unit of work, or roll it back if repository work fails."""
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
