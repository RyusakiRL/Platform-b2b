"""User management tests."""

from datetime import datetime, timezone

from models.enums import AccountRole
from models.workforce import Employee, Account
from security import create_token_jwt, verify_password


def create_requester_and_target(db_session, role, username):
    """Create a requester account and a target employee for testing."""
    requester_employee = Employee(
        full_name="Requester Employee",
        phone="1234567890",
        address="123 Test St",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )

    target_employee = Employee(
        full_name="Target Employee",
        phone="0987654321",
        address="456 Test St",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )

    db_session.add_all([requester_employee, target_employee])
    db_session.flush()

    requester_account = Account(
        username=username,
        password_hash="unused-hash-in-this-test",
        employee_id=requester_employee.id,
        role=role,
        is_active=True,
    )

    db_session.add(requester_account)
    db_session.commit()

    return requester_account.id, target_employee.id


def test_manager_cannot_create_another_manager(client, db_session):
    """Test that a manager cannot create another manager."""
    requester_id, target_employee_id = create_requester_and_target(
        db_session=db_session,
        role=AccountRole.MANAGER,
        username="manager_test",
    )

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

    created_account = (
        db_session.query(Account).filter(Account.username == "new_manager").first()
    )
    assert created_account is None


def test_administrator_can_create_manager(client, db_session):
    """Test that an administrator can create a new manager account."""
    requester_id, target_employee_id = create_requester_and_target(
        db_session=db_session,
        role=AccountRole.ADMINISTRATOR,
        username="admin_test",
    )

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

    assert response.status_code == 200
    assert response.json() == {"message": "Manager created successfully."}

    created_account = (
        db_session.query(Account).filter(Account.username == "new_manager").first()
    )

    assert created_account is not None
    assert created_account.role == AccountRole.MANAGER
    assert created_account.employee_id == target_employee_id
    assert created_account.password_hash != "senhaforte123"
    assert verify_password("senhaforte123", created_account.password_hash)


def test_create_manager_with_nonexistent_employee(client, db_session):
    """Test that creating a manager with a non-existent employee ID fails."""
    requester_id, _ = create_requester_and_target(
        db_session=db_session,
        role=AccountRole.ADMINISTRATOR,
        username="admin_test2",
    )

    token = create_token_jwt({"sub": str(requester_id)})

    response = client.post(
        "/users/manager/create",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "new_manager2",
            "password": "senhaforte123",
            "employee_id": 9999,
            "role_user": "manager",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Active employee not found."}

    created_account = (
        db_session.query(Account).filter(Account.username == "new_manager2").first()
    )
    assert created_account is None


def test_create_manager_with_innactive_employee(client, db_session):
    """Test that creating a manager with an inactive employee fails."""
    requester_id, target_employee_id = create_requester_and_target(
        db_session=db_session,
        role=AccountRole.ADMINISTRATOR,
        username="admin_test3",
    )

    target_employee = (
        db_session.query(Employee).filter(Employee.id == target_employee_id).first()
    )
    target_employee.is_active = False
    db_session.commit()

    token = create_token_jwt({"sub": str(requester_id)})

    response = client.post(
        "/users/manager/create",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "new_manager3",
            "password": "senhaforte123",
            "employee_id": target_employee_id,
            "role_user": "manager",
        },
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Active employee not found."}

    created_account = (
        db_session.query(Account).filter(Account.username == "new_manager3").first()
    )
    assert created_account is None


def test_create_manager_when_employee_already_has_account(client, db_session):
    """Test that creating a manager for an employee who already has an account fails."""
    requester_id, target_employee_id = create_requester_and_target(
        db_session=db_session,
        role=AccountRole.ADMINISTRATOR,
        username="admin_test4",
    )

    existing_account = Account(
        username="existing_account",
        password_hash="unused-hash-in-this-test",
        employee_id=target_employee_id,
        role=AccountRole.MANAGER,
        is_active=True,
    )
    db_session.add(existing_account)
    db_session.commit()

    token = create_token_jwt({"sub": str(requester_id)})

    response = client.post(
        "/users/manager/create",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "new_manager4",
            "password": "senhaforte123",
            "employee_id": target_employee_id,
            "role_user": "manager",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "This employee already has an account."}

    created_account = (
        db_session.query(Account).filter(Account.username == "new_manager4").first()
    )
    assert created_account is None


def test_create_manager_with_duplicate_username(client, db_session):
    """Test that creating a manager with a duplicate username fails."""
    requester_id, target_employee_id = create_requester_and_target(
        db_session=db_session,
        role=AccountRole.ADMINISTRATOR,
        username="admin_test5",
    )

    existing_account = Account(
        username="duplicate_username",
        password_hash="unused-hash-in-this-test",
        employee_id=target_employee_id,
        role=AccountRole.MANAGER,
        is_active=True,
    )
    other_employee = Employee(
        full_name="Other Employee",
        phone="1112223333",
        address="789 Test St",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(other_employee)
    db_session.add(existing_account)
    db_session.commit()

    token = create_token_jwt({"sub": str(requester_id)})

    response = client.post(
        "/users/manager/create",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "username": "duplicate_username",
            "password": "senhaforte123",
            "employee_id": other_employee.id,
            "role_user": "manager",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Username already exists."}

    created_account = (
        db_session.query(Account).filter(Account.username == "duplicate_username").all()
    )
    assert len(created_account) == 1
