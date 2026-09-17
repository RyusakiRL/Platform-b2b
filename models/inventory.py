"""Inventory models for the application"""

from datetime import datetime, timezone

from sqlalchemy.orm import relationship
from sqlalchemy import (
    Integer,
    Numeric,
    String,
    ForeignKey,
    Column,
    DateTime,
    Boolean,
    Enum,
    CheckConstraint,
    UniqueConstraint,
)
from models.base import Base
from models.enums import MovementType


class CurrentInventory(Base):
    """Table template for enterprise products inventory"""

    __tablename__ = "current_inventory"
    id = Column(Integer, primary_key=True, index=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    product_in_stock = Column(Integer, default=0, nullable=False)
    product_to_come = Column(Integer, default=0, nullable=False)
    warehouse_id = Column(
        Integer, ForeignKey("warehouses.id"), nullable=False, index=True
    )

    product_relationship = relationship(
        "Product", back_populates="inventory_relationship"
    )
    movement_relationship = relationship(
        "InventoryMovement", back_populates="current_inventory_relationship"
    )
    warehouse_inv_relationship = relationship(
        "Warehouse", back_populates="inventory_ware_relationship"
    )
    __table_args__ = (
        CheckConstraint("product_in_stock >=0", name="ck_product_non_negative"),
        CheckConstraint("product_to_come >= 0", name="ck_product_to_come_non_negative"),
        UniqueConstraint(
            "warehouse_id",
            "product_id",
            name="uq_inventory_warehouse_product",
        ),
    )


class Product(Base):
    """Template for creation products names"""

    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    sku = Column(String(50), nullable=False, unique=True)
    product_name = Column(String(255), nullable=False)
    base_price = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    inventory_relationship = relationship(
        "CurrentInventory", back_populates="product_relationship"
    )
    __table_args__ = (
        CheckConstraint(
            "base_price >= 0",
            name="ck_product_price_nonnegative",
        ),
    )


class InventoryMovement(Base):
    """Table template for inventory movement"""

    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True, index=True)
    current_inventory_id = Column(
        Integer, ForeignKey("current_inventory.id"), nullable=False, index=True
    )
    created_by_account_id = Column(
        Integer,
        ForeignKey("accounts.id"),
        nullable=False,
        index=True,
    )
    movement_type = Column(Enum(MovementType), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_at_transaction = Column(Numeric(12, 2), nullable=False)
    timestamp = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    current_inventory_relationship = relationship(
        "CurrentInventory", back_populates="movement_relationship"
    )
    account = relationship("Account", back_populates="inventory_movements")
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_quantity_positive"),
        CheckConstraint(
            "unit_price_at_transaction >= 0", name="ck_unit_price_non_negative"
        ),
    )


class Warehouse(Base):
    """Table template for warehouse creation"""

    __tablename__ = "warehouses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), nullable=False)
    address = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    inventory_ware_relationship = relationship(
        "CurrentInventory", back_populates="warehouse_inv_relationship"
    )
