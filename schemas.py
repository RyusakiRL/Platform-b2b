"""Data validation based em class models"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

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
    card_number: str = Field(min_length=6, max_length=6)
