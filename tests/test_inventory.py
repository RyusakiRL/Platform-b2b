"""Pytest for inventory module."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from fastapi import HTTPException
from services.inventory_service import apply_inventory_movement
from models.inventory import CurrentInventory, Warehouse, Product
from models.workforce import Account, AccountRole, Employee
from models.enums import MovementType


@pytest.fixture(name="inventory_context")
def fixture_inventory_context(db_session):
    """Create valid dependencies for inventory stests."""

    employee = Employee(
        full_name="Test Manager",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(employee)
    db_session.flush()  # Gera employee.id sem precisar fazer commit

    account = Account(
        employee_id=employee.id,
        username="manager_test",
        password_hash="unused-hash-in-unit-tests",
        role=AccountRole.MANAGER,
        is_active=True,
    )

    product = Product(
        sku="TEST-001",
        product_name="Test Product",
        base_price=Decimal("5.00"),
        is_active=True,
    )

    warehouse = Warehouse(
        name="Test Warehouse",
        address="123 Test St",
        is_active=True,
    )

    db_session.add_all([account, product, warehouse])
    db_session.commit()

    db_session.refresh(account)
    db_session.refresh(product)
    db_session.refresh(warehouse)

    return {
        "employee": employee,
        "account": account,
        "product": product,
        "warehouse": warehouse,
    }


def test_in_movement_creates_inventory(db_session, inventory_context):
    """Test that an IN movement creates a new inventory record."""
    product = inventory_context["product"]
    warehouse = inventory_context["warehouse"]
    account = inventory_context["account"]

    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.IN,
        quantity=10,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=product.id,
            warehouse_id=warehouse.id,
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == 10


def test_in_movement_increases_existing_stock(db_session, inventory_context):
    """Test that an IN movement increases existing stock."""
    product = inventory_context["product"]
    warehouse = inventory_context["warehouse"]
    account = inventory_context["account"]
    initial_quantity = 5
    additional_quantity = 10

    # Create initial inventory record
    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.IN,
        quantity=initial_quantity,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    # Apply additional IN movement
    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.IN,
        quantity=additional_quantity,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=product.id,
            warehouse_id=warehouse.id,
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == initial_quantity + additional_quantity


def test_out_movement_decreases_stock(db_session, inventory_context):
    """Test that an OUT movement decreases existing stock."""
    product = inventory_context["product"]
    warehouse = inventory_context["warehouse"]
    account = inventory_context["account"]
    initial_quantity = 15
    out_quantity = 5

    # Create initial inventory record
    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.IN,
        quantity=initial_quantity,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    # Apply OUT movement
    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.OUT,
        quantity=out_quantity,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=product.id,
            warehouse_id=warehouse.id,
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == initial_quantity - out_quantity


def test_out_without_inventory_returns(db_session, inventory_context):
    """Test that an out movement without existing inventory raises an error."""
    product = inventory_context["product"]
    warehouse = inventory_context["warehouse"]
    account = inventory_context["account"]
    with pytest.raises(HTTPException) as exc_info:
        apply_inventory_movement(
            product_id=product.id,
            warehouse_id=warehouse.id,
            account_id=account.id,
            movement_type=MovementType.OUT,
            quantity=5,
            db=db_session,
            unit_price=Decimal("5.00"),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "No stock available for this product in this warehouse."
    )


def test_out_without_enough_inventory_returns(db_session, inventory_context):
    """Test that an out movement with insufficient stock raises an error."""
    product = inventory_context["product"]
    warehouse = inventory_context["warehouse"]
    account = inventory_context["account"]
    initial_quantity = 5
    retired_quantity = 10

    # Create initial inventory record
    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.IN,
        quantity=initial_quantity,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    with pytest.raises(HTTPException) as exc_info:
        apply_inventory_movement(
            product_id=product.id,
            warehouse_id=warehouse.id,
            account_id=account.id,
            movement_type=MovementType.OUT,
            quantity=retired_quantity,  # Attempt to remove more than available
            db=db_session,
            unit_price=Decimal("5.00"),
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == ("Not enough stock for this movement.")


def test_failed_out_movement_does_not_change_inventory(db_session, inventory_context):
    """Test that a failed OUT movement does not change the inventory."""
    product = inventory_context["product"]
    warehouse = inventory_context["warehouse"]
    account = inventory_context["account"]
    initial_quantity = 5
    retired_quantity = 10
    # Create initial inventory record
    apply_inventory_movement(
        product_id=product.id,
        warehouse_id=warehouse.id,
        account_id=account.id,
        movement_type=MovementType.IN,
        quantity=initial_quantity,
        db=db_session,
        unit_price=Decimal("5.00"),
    )

    # Attempt to apply OUT movement that should fail
    with pytest.raises(HTTPException):
        apply_inventory_movement(
            product_id=product.id,
            warehouse_id=warehouse.id,
            account_id=account.id,
            movement_type=MovementType.OUT,
            quantity=retired_quantity,  # Attempt to remove more than available
            db=db_session,
            unit_price=Decimal("5.00"),
        )

    # Verify that the inventory remains unchanged
    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=product.id,
            warehouse_id=warehouse.id,
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == initial_quantity
