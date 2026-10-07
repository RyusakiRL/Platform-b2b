"""Configuration for pytest fixtures and test setup."""

import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "secret-key-used-only-in-tests"

# Estes imports precisam acontecer depois da configuração do ambiente.
# pylint: disable=wrong-import-position
from database import get_db
from main import app
from models import Base

engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TESTINGSESSIONLOCAL = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    """Create a new database session for testing and yield it."""
    db = TESTINGSESSIONLOCAL()

    try:
        yield db
    finally:
        db.close()


@event.listens_for(engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, _):
    """Enable foreign key constraints for SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


@pytest.fixture(autouse=True)
def setup_database():
    """Create the database tables before each test and drop them after."""
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.pop(get_db, None)
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    """Provide a database session for arranging and checking test data."""

    db = TESTINGSESSIONLOCAL()

    try:
        yield db
    finally:
        db.rollback()
        db.close()


@pytest.fixture
def client():
    """Provide the FastAPI test client."""

    with TestClient(app) as test_client:
        yield test_client
