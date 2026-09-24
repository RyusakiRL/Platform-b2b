"""Inventory service module for managing inventory movements."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_400_BAD_REQUEST,
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from models.inventory import CurrentInventory, InventoryMovement, Product, Warehouse
from models.workforce import Account
from models.enums import AccountRole, MovementType
from schemas import InventoryMovementValidation, ProductValidation, WarehouseValidation


def product_creation(
    product_validation: ProductValidation, current_account: Account, db: Session
):
    """Allow a manager to create a product"""
    if current_account.role not in [AccountRole.MANAGER, AccountRole.ADMINISTRATOR]:
        raise HTTPException(
            status_code=403,
            detail="Access denied: only active manager or administrator can create products.",
        )
    product_existence = (
        db.query(Product).filter(Product.sku == product_validation.sku).first()
    )
    if product_existence:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists.",
        )

    new_product = Product(
        sku=product_validation.sku,
        product_name=product_validation.product_name,
        base_price=product_validation.base_price,
    )
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return {"message": "Product created successfully."}


def inventory_movement_creation(
    data: InventoryMovementValidation,
    current_account: Account,
    db: Session,
):
    """Allow a manager to move products in/out of inventory"""
    if current_account.role not in [AccountRole.MANAGER, AccountRole.ADMINISTRATOR]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only active manager or administrator can create inventory move.",
        )
    product = db.query(Product).filter(Product.id == data.product_id).first()
    if not product or not product.is_active:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Product not found.",
        )
    warehouse = db.query(Warehouse).filter(Warehouse.id == data.warehouse_id).first()
    if not warehouse or not warehouse.is_active:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Warehouse not found.",
        )
    try:
        current_inventory = (
            (
                db.query(CurrentInventory).filter(
                    CurrentInventory.product_id == data.product_id,
                    CurrentInventory.warehouse_id == data.warehouse_id,
                )
            )
            .with_for_update()
            .first()
        )

        if current_inventory is None:
            if data.movement_type == MovementType.OUT:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="No stock available for this product in this warehouse.",
                )
            current_inventory = CurrentInventory(
                product_id=data.product_id,
                warehouse_id=data.warehouse_id,
                product_in_stock=0,
                product_to_come=0,
            )
            db.add(current_inventory)
            db.flush()
        if data.movement_type == MovementType.IN:
            current_inventory.product_in_stock += data.quantity
        else:
            if current_inventory.product_in_stock < data.quantity:
                raise HTTPException(
                    status_code=HTTP_400_BAD_REQUEST,
                    detail="Not enough stock for this movement.",
                )
            current_inventory.product_in_stock -= data.quantity
        new_inventory_movement = InventoryMovement(
            created_by_account_id=current_account.id,
            current_inventory_id=current_inventory.id,
            movement_type=data.movement_type,
            quantity=data.quantity,
            unit_price_at_transaction=data.unit_price_at_transaction,
        )
        db.add(new_inventory_movement)
        db.commit()
    except Exception:
        db.rollback()
        raise
    return {"message": "Inventory movement recorded successfully."}


def warehouse_creation(
    warehouse_validation: WarehouseValidation, current_account: Account, db: Session
):
    """Allow a administrator to create a warehouse"""
    if current_account.role != AccountRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only active administrator can create warehouses.",
        )
    warehouse_name_existence = (
        db.query(Warehouse).filter(Warehouse.name == warehouse_validation.name).first()
    )
    if warehouse_name_existence:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Warehouse with this name already exists.",
        )
    warehouse_address_existence = (
        db.query(Warehouse)
        .filter(Warehouse.address == warehouse_validation.address)
        .first()
    )
    if warehouse_address_existence:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Warehouse with this address already exists",
        )

    new_warehouse = Warehouse(
        name=warehouse_validation.name,
        address=warehouse_validation.address,
    )
    db.add(new_warehouse)
    db.commit()
    db.refresh(new_warehouse)
    return {"message": "Warehouse created successfully."}
