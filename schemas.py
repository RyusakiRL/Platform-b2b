"""Data validation based em class models"""

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from models.enums import AccountRole, PaymentType


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
    movement_type: PaymentType
    quantity: int = Field(gt=0)
