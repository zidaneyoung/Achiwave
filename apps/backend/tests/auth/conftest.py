import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker

BACKEND_ROOT = Path(__file__).parents[2]
TEST_DATABASE_ENV = "ACHIWAVE_TEST_DATABASE_URL"


@pytest.fixture(scope="session")
def auth_database_url() -> str:
    database_url = os.environ.get(TEST_DATABASE_ENV)
    if database_url is None:
        pytest.skip(f"{TEST_DATABASE_ENV} is not configured")
    database_name = make_url(database_url).database or ""
    if not any(marker in database_name.lower() for marker in ("test", "ci")):
        pytest.fail(
            f"Refusing authentication tests for unsafe database {database_name!r}"
        )

    previous_url = os.environ.get("ACHIWAVE_DATABASE_URL")
    os.environ["ACHIWAVE_DATABASE_URL"] = database_url
    try:
        command.upgrade(Config(str(BACKEND_ROOT / "alembic.ini")), "head")
    finally:
        if previous_url is None:
            os.environ.pop("ACHIWAVE_DATABASE_URL", None)
        else:
            os.environ["ACHIWAVE_DATABASE_URL"] = previous_url
    return database_url


@pytest.fixture(scope="session")
def auth_engine(auth_database_url: str) -> Iterator[Engine]:
    engine = create_engine(auth_database_url)
    try:
        yield engine
    finally:
        engine.dispose()


@pytest.fixture()
def auth_session_factory(
    auth_engine: Engine,
) -> Iterator[sessionmaker[Session]]:
    with auth_engine.begin() as connection:
        connection.execute(text("TRUNCATE TABLE users CASCADE"))
    factory = sessionmaker(
        bind=auth_engine,
        autoflush=False,
        expire_on_commit=False,
    )
    yield factory
