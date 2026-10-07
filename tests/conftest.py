"""Configuration for pytest fixtures and test setup."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from database import get_db
from main import app
from models import Base
import os

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "secret-key-used-only-in-tests"


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def override_get_db():
    """Create a new database session for testing and yield it."""
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


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

    db = TestingSessionLocal()

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
