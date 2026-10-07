"""Pytest for inventory module."""

import pytest
from fastapi import HTTPException
from services.inventory_service import apply_inventory_movement
from models.inventory import CurrentInventory, Warehouse
from models.enums import MovementType

inventory_movement_validation = {
    "product_id": 1,
    "warehouse_id": 1,
    "account_id": 1,
    "movement_type": MovementType.IN,
    "quantity": 10,
    "unit_price": 5.0,
}
warehouse_validation = {"name": "Test Warehouse", "address": "123 test St"}


def test_in_movement_creates_inventory(db_session):
    """Test that an IN movement creates a new inventory record."""
    new_warehouse = Warehouse(
        name=warehouse_validation["name"], address=warehouse_validation["address"]
    )
    db_session.add(new_warehouse)
    db_session.commit()
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        inventory_movement_validation["movement_type"],
        inventory_movement_validation["quantity"],
        db_session,
        inventory_movement_validation["unit_price"],
    )

    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=inventory_movement_validation["product_id"],
            warehouse_id=inventory_movement_validation["warehouse_id"],
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == inventory_movement_validation["quantity"]


def test_in_movement_increases_existing_stock(db_session):
    """Test that an IN movement increases existing stock."""
    initial_quantity = 5
    additional_quantity = 10
    new_warehouse = Warehouse(
        name=warehouse_validation["name"], address=warehouse_validation["address"]
    )
    db_session.add(new_warehouse)
    db_session.commit()
    # Create initial inventory record
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        inventory_movement_validation["movement_type"],
        initial_quantity,
        db_session,
        inventory_movement_validation["unit_price"],
    )

    # Apply additional IN movement
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        inventory_movement_validation["movement_type"],
        additional_quantity,
        db_session,
        inventory_movement_validation["unit_price"],
    )

    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=inventory_movement_validation["product_id"],
            warehouse_id=inventory_movement_validation["warehouse_id"],
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == initial_quantity + additional_quantity


def test_out_movement_decreases_stock(db_session):
    """Test that an OUT movement decreases existing stock."""
    initial_quantity = 15
    out_quantity = 5
    new_warehouse = Warehouse(
        name=warehouse_validation["name"], address=warehouse_validation["address"]
    )
    db_session.add(new_warehouse)
    db_session.commit()

    # Create initial inventory record
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        MovementType.IN,
        initial_quantity,
        db_session,
        inventory_movement_validation["unit_price"],
    )

    # Apply OUT movement
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        MovementType.OUT,
        out_quantity,
        db_session,
        inventory_movement_validation["unit_price"],
    )

    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=inventory_movement_validation["product_id"],
            warehouse_id=inventory_movement_validation["warehouse_id"],
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == initial_quantity - out_quantity


def test_out_without_inventory_returns(db_session):
    """Test that an out movement without existing inventory raises an error."""
    new_warehouse = Warehouse(
        name=warehouse_validation["name"], address=warehouse_validation["address"]
    )
    db_session.add(new_warehouse)
    db_session.commit()
    with pytest.raises(HTTPException) as exc_info:
        apply_inventory_movement(
            inventory_movement_validation["product_id"],
            inventory_movement_validation["warehouse_id"],
            inventory_movement_validation["account_id"],
            MovementType.OUT,
            5,
            db_session,
            inventory_movement_validation["unit_price"],
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == (
        "No stock available for this product in this warehouse."
    )


def test_out_without_enough_inventory_returns(db_session):
    """Test that an out movement with insufficient stock raises an error."""
    initial_quantity = 5
    retired_quantity = 10
    new_warehouse = Warehouse(
        name=warehouse_validation["name"], address=warehouse_validation["address"]
    )
    db_session.add(new_warehouse)
    db_session.commit()

    # Create initial inventory record
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        MovementType.IN,
        initial_quantity,
        db_session,
        inventory_movement_validation["unit_price"],
    )

    with pytest.raises(HTTPException) as exc_info:
        apply_inventory_movement(
            inventory_movement_validation["product_id"],
            inventory_movement_validation["warehouse_id"],
            inventory_movement_validation["account_id"],
            MovementType.OUT,
            retired_quantity,  # Attempt to remove more than available
            db_session,
            inventory_movement_validation["unit_price"],
        )

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == ("Not enough stock for this movement.")


def test_failed_out_movement_does_not_change_inventory(db_session):
    """Test that a failed OUT movement does not change the inventory."""
    initial_quantity = 5
    retired_quantity = 10
    new_warehouse = Warehouse(
        name=warehouse_validation["name"], address=warehouse_validation["address"]
    )
    db_session.add(new_warehouse)
    db_session.commit()

    # Create initial inventory record
    apply_inventory_movement(
        inventory_movement_validation["product_id"],
        inventory_movement_validation["warehouse_id"],
        inventory_movement_validation["account_id"],
        MovementType.IN,
        initial_quantity,
        db_session,
        inventory_movement_validation["unit_price"],
    )

    # Attempt to apply OUT movement that should fail
    with pytest.raises(HTTPException):
        apply_inventory_movement(
            inventory_movement_validation["product_id"],
            inventory_movement_validation["warehouse_id"],
            inventory_movement_validation["account_id"],
            MovementType.OUT,
            retired_quantity,  # Attempt to remove more than available
            db_session,
            inventory_movement_validation["unit_price"],
        )

    # Verify that the inventory remains unchanged
    inventory = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=inventory_movement_validation["product_id"],
            warehouse_id=inventory_movement_validation["warehouse_id"],
        )
        .first()
    )
    assert inventory is not None
    assert inventory.product_in_stock == initial_quantity
