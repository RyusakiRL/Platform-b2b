"""System tests."""

import os
from datetime import datetime, timezone

os.environ["DATABASE_URL"] = "sqlite://"
os.environ["SECRET_KEY"] = "secret-key-used-only-in-tests"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import get_db
from main import app
from models import Base
from models.enums import AccountRole
from models.workforce import Employee, Account
from security import create_token_jwt

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
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_manager_cannot_create_another_manager():
    """A manager cannot create another manager."""

    with TestingSessionLocal() as db:
        requester_employee = Employee(
            full_name="Manager Test",
            phone="1234567890",
            address="123 Test St",
            hired_at=datetime.now(timezone.utc),
            is_active=True,
        )

        target_employee = Employee(
            full_name="New Manager Employee",
            phone="0987654321",
            address="456 Test St",
            hired_at=datetime.now(timezone.utc),
            is_active=True,
        )

        db.add_all([requester_employee, target_employee])
        db.flush()

        requester_account = Account(
            username="manager_test",
            password_hash="unused-hash-in-this-test",
            employee_id=requester_employee.id,
            role=AccountRole.MANAGER,
            is_active=True,
        )

        db.add(requester_account)
        db.commit()

        requester_id = requester_account.id
        target_employee_id = target_employee.id

    token = create_token_jwt({"sub": str(requester_id)})

    response = client.post(
        "/users/manager/create",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "new_manager",
            "password": "senhaforte123",
            "employee_id": target_employee_id,
            "role_user": "manager",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "Access denied: only administrator can create managers."
    }
