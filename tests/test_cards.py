"""Cards tests module."""

from datetime import datetime, timezone
from uuid import UUID
import pytest
from models.workforce import Account, AccountRole, Employee, Card
from security import create_token_jwt


@pytest.fixture(name="cards_context")
def fixture_cards_context(db_session):
    """Create valid dependencies for card tests."""
    employee = Employee(
        full_name="Test Manager",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(employee)
    db_session.flush()

    account = Account(
        employee_id=employee.id,
        username="manager_test",
        password_hash="unused-hash-in-unit-tests",
        role=AccountRole.MANAGER,
        is_active=True,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(employee)
    db_session.refresh(account)

    return {"employee": employee, "account": account}


def test_manager_can_create_card(db_session, cards_context):
    """Test that a manager can create a card."""
    employee = cards_context["employee"]

    new_card = Card(
        card_number="1234567890123456",
        employee_id=employee.id,
        is_active=True,
    )
    db_session.add(new_card)
    db_session.commit()

    created_card = (
        db_session.query(Card).filter_by(card_number="1234567890123456").first()
    )
    assert created_card is not None
    assert created_card.employee_id == employee.id


def test_card_number_is_valid_uuid(client, cards_context):
    """Test that the generated card number is a valid UUID4."""
    employee = cards_context["employee"]
    account = cards_context["account"]

    token = create_token_jwt({"sub": str(account.id)})

    response = client.post(
        "/cards/create",
        headers={"Authorization": f"Bearer {token}"},
        json={"employee_id": employee.id},
    )

    assert response.status_code == 200, response.text

    card_number = response.json()["qr_code"]
    parsed_uuid = UUID(card_number)

    assert parsed_uuid.version == 4
    assert str(parsed_uuid) == card_number


def test_employee_cannot_have_multiple_active_cards(db_session, client, cards_context):
    """Test that an employee cannot have multiple active cards."""
    employee = cards_context["employee"]
    account = cards_context["account"]

    # Create the first active card
    first_card = Card(
        card_number="1111111111111111",
        employee_id=employee.id,
        is_active=True,
    )

    db_session.add(first_card)
    db_session.commit()

    token = create_token_jwt({"sub": str(account.id)})

    # Attempt to create a second active card for the same employee
    response = client.post(
        "/cards/create",
        headers={"Authorization": f"Bearer {token}"},
        json={"employee_id": employee.id},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Employee already have a active card"


def test_disable_card_makes_inactive(db_session, client, cards_context):
    """Test that disabling a card makes it inactive."""
    employee = cards_context["employee"]
    account = cards_context["account"]

    # Create an active card
    card = Card(
        card_number="2222222222222222",
        employee_id=employee.id,
        is_active=True,
    )
    db_session.add(card)
    db_session.commit()

    token = create_token_jwt({"sub": str(account.id)})

    # Disable the card
    response = client.patch(
        f"/cards/disable/{card.id}",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    db_session.refresh(card)
    assert not card.is_active


def test_disable_missing_card_returns_404(client, cards_context):
    """Test that disabling a non-existent card returns a 404 error."""
    account = cards_context["account"]

    token = create_token_jwt({"sub": str(account.id)})

    # Attempt to disable a card with a non-existent ID
    response = client.patch(
        "/cards/disable/9999",  # Assuming 9999 is a non-existent card ID
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Card not found"


def test_cannot_create_card_for_inactive_employee(db_session, client, cards_context):
    """Test that a card cannot be created for an inactive employee."""
    employee = cards_context["employee"]
    account = cards_context["account"]

    # Deactivate the employee
    employee.is_active = False
    db_session.commit()

    token = create_token_jwt({"sub": str(account.id)})

    # Attempt to create a card for the inactive employee
    response = client.post(
        "/cards/create",
        headers={"Authorization": f"Bearer {token}"},
        json={"employee_id": employee.id},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Cannot create card for inactive employee"
