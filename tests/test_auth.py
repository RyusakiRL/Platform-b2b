"""Pytest for the auth module."""

from datetime import datetime, timezone
from models.workforce import Account, Employee
from models.enums import AccountRole
from security import generator_hash_password, create_token_jwt, timedelta


def create_test_account(db_session, role, username, password):
    """Create a test account with the specified role and username."""
    test_employee = Employee(
        full_name="Test Employee",
        phone="1234567890",
        address="123 Test St",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(test_employee)
    db_session.commit()

    password_hash = generator_hash_password(password)
    test_account = Account(
        username=username,
        password_hash=password_hash,
        employee_id=test_employee.id,
        role=role,
        is_active=True,
    )
    db_session.add(test_account)
    db_session.commit()
    return test_account


def test_login_success(client, db_session):
    """Test successful login."""
    flat_password = "securepassword123"
    create_test_account(db_session, AccountRole.MANAGER, "login_test", flat_password)
    response = client.post(
        "/auth/login",
        data={"username": "login_test", "password": flat_password},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert response.json()["token_type"] == "bearer"
    assert response.json()["access_token"] is not None


def test_login_invalid_password(client, db_session):
    """Test login with invalid password."""
    create_test_account(
        db_session, AccountRole.MANAGER, "invalid_test", "correctpassword"
    )
    response = client.post(
        "/auth/login",
        data={"username": "invalid_test", "password": "wrongpassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credential"


def test_login_invalid_username(client, db_session):
    """Test login with invalid username."""
    create_test_account(db_session, AccountRole.MANAGER, "valid_user", "somepassword")
    response = client.post(
        "/auth/login",
        data={"username": "nonexistent_user", "password": "somepassword"},
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid credential"


def test_login_inactive_account(client, db_session):
    """Test login with an inactive account."""
    flat_password = "inactivepassword"
    test_account = create_test_account(
        db_session, AccountRole.MANAGER, "inactive_user", flat_password
    )
    # Deactivate the account
    test_account.is_active = False
    db_session.commit()

    response = client.post(
        "/auth/login",
        data={"username": "inactive_user", "password": flat_password},
    )
    assert response.status_code == 403
    assert response.json()["detail"] == "Account is inactive"


def test_request_token_without_token_returns(client):
    """Test accessing a protected endpoint without a token."""
    response = client.post("users/employee/create")
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"


def test_request_token_with_invalid_token_returns(client):
    """Test accessing a protected endpoint with an invalid token."""
    response = client.post(
        "users/employee/create", headers={"Authorization": "Bearer invalidtoken"}
    )
    assert response.status_code == 401


def test_request_token_with_expired_token_returns(client, db_session):
    """Test accessing a protected endpoint with an expired token."""
    # Create a test account and generate an expired token
    flat_password = "expiredpassword"
    create_test_account(
        db_session=db_session,
        role=AccountRole.MANAGER,
        username="expired_user",
        password=flat_password,
    )

    login = client.post(
        "/auth/login",
        data={"username": "expired_user", "password": flat_password},
    )
    assert login.status_code == 200

    expired_token = create_token_jwt(
        {"sub": str(login.json()["access_token"])},
        expires_delta=timedelta(minutes=-1),
    )

    response = client.post(
        "/users/employee/create",
        headers={"Authorization": f"Bearer {expired_token}"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid or expired badge"
