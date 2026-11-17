"""Router for inventory-related endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from schemas import (
    InventoryMovementValidation,
    ProductValidation,
    WarehouseValidation,
    InventoryMovementResponse,
    CurrentInventoryResponse,
)
from dependencies import get_current_account
from models.workforce import Account
from services.inventory_service import (
    product_creation,
    inventory_movement_creation,
    warehouse_creation,
    get_warehouse_inventory,
    get_current_inventory,
    get_stock_movements,
    get_inventory_movements_by_warehouse,
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


@router.get(
    "/warehouses/{warehouse_id}/products/{product_id}",
    dependencies=[Depends(get_current_account)],
    response_model=CurrentInventoryResponse,
)
def get_current_inventory_route(
    warehouse_id: int,
    product_id: int,
    db: Session = Depends(get_db),
):
    """Get the current inventory of a product in a specific warehouse."""
    return get_current_inventory(
        product_id=product_id,
        warehouse_id=warehouse_id,
        db=db,
    )


@router.get(
    "/warehouses/{warehouse_id}/inventory",
    dependencies=[Depends(get_current_account)],
    response_model=list[CurrentInventoryResponse],
)
def get_warehouse_inventory_route(
    warehouse_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get the paginated inventory of a warehouse."""
    return get_warehouse_inventory(
        warehouse_id=warehouse_id,
        db=db,
        offset=offset,
        limit=limit,
    )


@router.get(
    "/warehouses/{warehouse_id}/products/{product_id}/movements",
    dependencies=[Depends(get_current_account)],
    response_model=list[InventoryMovementResponse],
)
def get_stock_movements_route(
    warehouse_id: int,
    product_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get the stock movements of a specific product in a specific warehouse."""
    return get_stock_movements(
        product_id=product_id,
        warehouse_id=warehouse_id,
        offset=offset,
        limit=limit,
        db=db,
    )


@router.get(
    "/warehouses/{warehouse_id}/movements",
    dependencies=[Depends(get_current_account)],
    response_model=list[InventoryMovementResponse],
)
def get_inventory_movements_by_warehouse_route(
    warehouse_id: int,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get the inventory movements of a specific warehouse."""
    return get_inventory_movements_by_warehouse(
        warehouse_id=warehouse_id,
        db=db,
        offset=offset,
        limit=limit,
    )
