"""Data validation based em class models"""

from typing import Literal
from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class ManagerAdministratorValidation(BaseModel):
    """Data validation for manager and administrator creation in SQL"""

    name_user: str = Field(min_length=3, max_length=50)
    password_user: str = Field(min_length=8, max_length=50)
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str):
        """returns the username in lowercase andd whitout whitespaces"""
        return value.strip().lower()


class OperatorValidation(BaseModel):
    """Data validation for operator creation in SQL"""

    name_user: str = Field(min_length=3, max_length=50)
    password_user: str = Field(min_length=8, max_length=50)
    username: str = Field(
        min_length=3,
        max_length=30,
        pattern=r"^[a-zA-Z0-9_.-]+$",
    )

    @field_validator("username", mode="before")
    @classmethod
    def normalize_username(cls, value: str):
        """returns the username in lowercase andd whitout whitespaces"""
        return value.strip().lower


class DepartmentValidation(BaseModel):
    """Data validation for department creation in SQL"""

    department_title: str = Field(min_length=3, max_length=100)
    users_id: int = Field(gt=0, description="User ID must be a positive integer")


class ProductValidation(BaseModel):
    """Data validation for product creation in SQL"""

    product_name: str = Field(min_length=3, max_length=100)
    base_price: float = Field(gt=0, description="Base price must be greater than zero")


class InventoryMovementValidation(BaseModel):
    """Data validation for moving products in/out of inventory"""

    product_id: int = Field(gt=0, description="Product ID must be a positive integer")
    departments_id: int = Field(
        gt=0, description="Department ID must be a positive integer"
    )
    movement_type: Literal["IN", "OUT"] = Field(
        description="Movement type must be 'IN' or 'OUT'"
    )
    quantity: int = Field(gt=0, description="Quantity must be greater than zero")


class CardValidation(BaseModel):
    """Data validation for card creation in SQL"""

    users_id: int = Field(gt=0, description="User ID must be a positive integer")


class RequiredColumns(BaseModel):
    """Data validation for required columns in Excel file"""

    name: str = Field(min_length=3, max_length=100)
    price: float = Field(gt=0, description="Price must be greater than zero")
    quantity: int = Field(gt=0, description="Quantity must be greater than zero")
    timestamp: datetime = Field(description="Timestamp must be in ISO 8601 format")
    movement_type: Literal["IN", "OUT"] = Field(
        description="Movement type must be 'IN' or 'OUT'"
    )
    department_id: int = Field(
        gt=0, description="Department ID must be a positive integer"
    )
