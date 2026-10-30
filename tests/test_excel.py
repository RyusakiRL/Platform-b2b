"""Excel tests module."""

from datetime import datetime, timezone
from io import BytesIO
import pytest
import pandas as pd
from decimal import Decimal
from models.enums import MovementType
from models.workforce import Account, AccountRole, Employee
from models.inventory import Product, CurrentInventory, Warehouse
from security import create_token_jwt


@pytest.fixture(name="excel_context")
def fixture_excel_context(db_session):
    """Create an authenticated manager for Excel tests."""

    employee = Employee(
        full_name="Excel Test Manager",
        hired_at=datetime.now(timezone.utc),
        is_active=True,
    )
    db_session.add(employee)
    db_session.flush()

    account = Account(
        employee_id=employee.id,
        username="excel_manager",
        password_hash="unused-hash-in-tests",
        role=AccountRole.MANAGER,
        is_active=True,
    )
    db_session.add(account)
    db_session.commit()
    db_session.refresh(account)

    warehouse = Warehouse(
        name="Excel Test Warehouse",
        address="Test Address",
        is_active=True,
    )

    db_session.add(warehouse)
    db_session.commit()
    db_session.refresh(warehouse)

    return {
        "account": account,
        "warehouse": warehouse,
    }


def test_rejects_non_xlsx_file(client, excel_context):
    """Test that the endpoint rejects a non-xlsx file."""

    account = excel_context["account"]
    token = create_token_jwt({"sub": str(account.id)})

    response = client.post(
        "/excel/upload/inventory",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "test.txt",
                b"Not an Excel file",
                "text/plain",
            )
        },
    )

    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid file format. Use .xlsx"}


def test_rejects_corrupted_xlsx_file(client, excel_context):
    """Test that the endpoint rejects a corrupted xlsx file."""

    account = excel_context["account"]
    token = create_token_jwt({"sub": str(account.id)})

    response = client.post(
        "/excel/upload/inventory",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "corrupted.xlsx",
                b"This is not a real Excel file",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 400, response.text
    assert response.json() == {"detail": "Invalid or corrupted Excel file."}


def test_valid_excel_creates_product_and_stock(
    client,
    db_session,
    excel_context,
):
    """Test that a valid Excel file creates products and stock."""

    account = excel_context["account"]
    warehouse = excel_context["warehouse"]
    token = create_token_jwt({"sub": str(account.id)})

    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

    data = {
        "name": ["Product A", "Product B"],
        "sku": ["SKU001", "SKU002"],
        "quantity": [10, 5],
        "timestamp": [timestamp, timestamp],
        "movement_type": [MovementType.IN.value, MovementType.IN.value],
        "price": [100.0, 200.0],
        "warehouse_id": [warehouse.id, warehouse.id],
    }

    excel_file = BytesIO()
    pd.DataFrame(data).to_excel(excel_file, index=False)
    excel_file.seek(0)

    response = client.post(
        "/excel/upload/inventory",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "valid.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )

    assert response.status_code == 200, response.text

    body = response.json()

    assert body["rows_processed"] == 2
    assert body["new_products_cataloged"] == 2
    assert body["inventory_movements_recorded"] == 2
    assert body["error_found"] == []

    db_session.expire_all()

    product_a = db_session.query(Product).filter_by(sku="SKU001").one()
    product_b = db_session.query(Product).filter_by(sku="SKU002").one()

    stock_a = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=product_a.id,
            warehouse_id=warehouse.id,
        )
        .one()
    )

    stock_b = (
        db_session.query(CurrentInventory)
        .filter_by(
            product_id=product_b.id,
            warehouse_id=warehouse.id,
        )
        .one()
    )

    assert stock_a.product_in_stock == 10
    assert stock_b.product_in_stock == 5


def test_excel_with_unknown_warehouse(client, excel_context):
    """Test that an Excel file with an unknown warehouse is rejected."""

    account = excel_context["account"]
    token = create_token_jwt({"sub": str(account.id)})

    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

    data = {
        "name": ["Product C"],
        "sku": ["SKU003"],
        "quantity": [15],
        "timestamp": [timestamp],
        "movement_type": [MovementType.IN.value],
        "price": [150.0],
        "warehouse_id": [9999],  # Non-existent warehouse ID
    }

    excel_file = BytesIO()
    pd.DataFrame(data).to_excel(excel_file, index=False)
    excel_file.seek(0)

    response = client.post(
        "/excel/upload/inventory",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "unknown_warehouse.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200, response.text

    body = response.json()

    errors = body["error_found"]

    assert len(errors) == 1
    assert errors[0]["excel_row"] == 2
    assert "9999" in errors[0]["errors"]
    assert "warehouse" in errors[0]["errors"].lower()


def test_excel_out_with_insufficient_stock(client, db_session, excel_context):
    """Test that an Excel file with an OUT movement exceeding stock is rejected."""

    account = excel_context["account"]
    warehouse = excel_context["warehouse"]
    token = create_token_jwt({"sub": str(account.id)})

    # Create a product and add stock
    product = Product(
        product_name="Product D",
        sku="SKU004",
        base_price=Decimal("50.00"),
    )
    db_session.add(product)
    db_session.commit()

    current_inventory = CurrentInventory(
        product_id=product.id,
        warehouse_id=warehouse.id,
        product_in_stock=5,
    )
    db_session.add(current_inventory)
    db_session.commit()

    timestamp = datetime.now(timezone.utc).replace(tzinfo=None)

    data = {
        "name": ["Product D"],
        "sku": ["SKU004"],
        "quantity": [10],  # Exceeds available stock
        "timestamp": [timestamp],
        "movement_type": [MovementType.OUT.value],
        "price": [50.0],
        "warehouse_id": [warehouse.id],
    }

    excel_file = BytesIO()
    pd.DataFrame(data).to_excel(excel_file, index=False)
    excel_file.seek(0)

    response = client.post(
        "/excel/upload/inventory",
        headers={"Authorization": f"Bearer {token}"},
        files={
            "file": (
                "insufficient_stock.xlsx",
                excel_file,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert response.status_code == 200, response.text

    assert response.status_code == 200, response.text

    body = response.json()
    errors = body["error_found"]

    assert body["rows_processed"] == 1
    assert body["new_products_cataloged"] == 0
    assert body["inventory_movements_recorded"] == 0

    assert len(errors) == 1
    assert errors[0]["excel_row"] == 2
    assert errors[0]["errors"] == "Not enough stock for this movement."
    db_session.expire_all()

    updated_inventory = db_session.get(
        CurrentInventory,
        current_inventory.id,
    )

    assert updated_inventory.product_in_stock == 5
