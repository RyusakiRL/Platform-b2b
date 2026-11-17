"""Data validation based em class models"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, UUID4, ConfigDict

from models.enums import AccountRole, MovementType


class EmployeeValidation(BaseModel):
    """Data validation for employee creation"""

    full_name: str = Field(min_length=3, max_length=100)
    phone: str | None = Field(None, max_length=20)
    address: str | None = Field(None, max_length=255)
    hired_at: datetime


class AccountValidation(BaseModel):
    """Data validation for account creation"""

    employee_id: int = Field(gt=0)
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=6, max_length=100)
    role_user: AccountRole


class ProductValidation(BaseModel):
    """Data validation for product creation"""

    sku: str = Field(min_length=3, max_length=50)
    product_name: str = Field(min_length=3, max_length=100)
    base_price: Decimal = Field(gt=0)


class InventoryMovementValidation(BaseModel):
    """Data validation for inventory movement creation"""

    product_id: int = Field(gt=0)
    warehouse_id: int = Field(gt=0)
    movement_type: MovementType
    quantity: int = Field(gt=0)
    unit_price_at_transaction: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class WarehouseValidation(BaseModel):
    """Data validation for warehouse creation"""

    name: str = Field(min_length=3, max_length=50)
    address: str = Field(min_length=3, max_length=255)


class CardValidation(BaseModel):
    """Data validation for card creation"""

    employee_id: int = Field(gt=0)


class InventoryRequiredColumns(BaseModel):
    """Data validation for excel inventory process"""

    name: str = Field(min_length=3, max_length=50)
    sku: str = Field(min_length=3, max_length=50)
    quantity: int = Field(gt=0)
    timestamp: datetime
    movement_type: MovementType
    price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    warehouse_id: int


class CardLookup(BaseModel):
    """Card lookup model for card validation"""

    card_number: UUID4


class CurrentInventoryResponse(BaseModel):
    """Response containing a product's stock in a warehouse."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    warehouse_id: int
    product_in_stock: int = Field(ge=0)
    product_to_come: int = Field(ge=0)
    created_at: datetime
    updated_at: datetime


class InventoryMovementResponse(BaseModel):
    """Response containing an inventory movement."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    current_inventory_id: int
    created_by_account_id: int
    movement_type: MovementType
    quantity: int = Field(gt=0)
    unit_price_at_transaction: Decimal = Field(
        ge=0,
        max_digits=12,
        decimal_places=2,
    )
    timestamp: datetime
