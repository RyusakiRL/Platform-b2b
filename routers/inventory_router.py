"""Router for inventory-related endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import InventoryMovementValidation, ProductValidation, WarehouseValidation
from dependencies import get_current_account
from models.workforce import Account
from services.inventory_service import (
    product_creation,
    inventory_movement_creation,
    warehouse_creation,
)

router = APIRouter(prefix="/inventory", tags=["Inventory management"])


@router.post("/product/create")
def create_product_route(
    product_validation: ProductValidation,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to create a product."""
    return product_creation(
        product_validation=product_validation,
        current_account=current_account,
        db=db,
    )


@router.post("/movement/create")
def create_inventory_movement_route(
    inventory_movement_validation: InventoryMovementValidation,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to create an inventory movement."""
    return inventory_movement_creation(
        data=inventory_movement_validation,
        current_account=current_account,
        db=db,
    )


@router.post("/warehouse/create")
def warehouse_creation_route(
    warehouse_val: WarehouseValidation,
    current_account: Account = Depends(get_current_account),
    db=Depends(get_db),
):
    """Endpoint to create a warehouse"""
    return warehouse_creation(
        current_account=current_account, warehouse_validation=warehouse_val, db=db
    )
