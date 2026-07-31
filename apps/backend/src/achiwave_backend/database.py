from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from achiwave_backend.config import Settings


class Base(DeclarativeBase):
    """Shared metadata base for future domain models."""


SessionFactory = sessionmaker[Session]


def create_database_engine(settings: Settings) -> Engine:
    """Create a PostgreSQL engine without connecting at import time."""
    return create_engine(
        settings.require_database_url(),
        connect_args={
            "connect_timeout": settings.database_connect_timeout_seconds,
        },
        max_overflow=settings.database_max_overflow,
        pool_pre_ping=True,
        pool_size=settings.database_pool_size,
        pool_timeout=settings.database_pool_timeout_seconds,
    )


def create_session_factory(engine: Engine) -> SessionFactory:
    return sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


@contextmanager
def session_scope(session_factory: SessionFactory) -> Iterator[Session]:
    """Provide one session and always release its connection."""
    session = session_factory()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
