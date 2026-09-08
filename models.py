"""Table creation templates in SQL"""

from datetime import datetime, timezone
import enum
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy import (
    Integer,
    String,
    ForeignKey,
    Column,
    DateTime,
    Float,
    Boolean,
    Enum,
)

NORMAL_OPERATOR_SALARY_HOUR = 1200.00
Base = declarative_base()


class AccountRole(enum.Enum):
    """Role for account acess levels"""

    ADMINISTRATOR = "administrator"
    MANAGER = "manager"


class Employee(Base):
    """Employee table template for creation of employees"""

    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    hired_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    account_relationship = relationship(
        "Account",
        back_populates="employee_relationship",
        uselist=False,
    )

    card_relationship = relationship(
        "Card",
        back_populates="employee_relationship",
    )

    time_records_relationship = relationship(
        "TimeRecord",
        back_populates="employee_relationship",
    )

    payroll_relationship = relationship(
        "MonthlyPayroll",
        back_populates="employee_payment_relationship",
    )
    managed_department = relationship("Department", back_populates="manager")


class Account(Base):
    """Account to access the system, linked to an employee"""

    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        unique=True,
    )

    username = Column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
    )

    password_hash = Column(String, nullable=False)
    role = Column(Enum(AccountRole), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    employee_relationship = relationship(
        "Employee",
        back_populates="account_relationship",
    )


class Department(Base):
    """Template for Department creation"""

    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    employees_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    department_title = Column(String, nullable=False)
    department_removed = Column(Boolean, default=False)
    manager = relationship("Employee", back_populates="managed_department")
    inventory_relationship = relationship(
        "CurrentInventory", back_populates="department_relationship"
    )


class TimeRecord(Base):
    """Table template for time record creation"""

    __tablename__ = "time_records"
    id = Column(
        Integer,
        primary_key=True,
    )
    employees_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    clock_in = Column(DateTime, nullable=False)
    clock_out = Column(DateTime, nullable=True)
    hour_worked = Column(Float, nullable=True)
    employee_relationship = relationship(
        "Employee", back_populates="time_records_relationship"
    )


class MonthlyPayroll(Base):
    """Table template for monthly payment"""

    __tablename__ = "monthly_payroll"
    id = Column(Integer, primary_key=True, index=True)
    employees_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    datetime_payment = Column(DateTime, nullable=False)
    base_salary = Column(Float, nullable=False)
    overtime_pay = Column(Float, nullable=False)
    tax_deductions = Column(Float, nullable=False)
    employee_payment_relationship = relationship(
        "Employee", back_populates="payment_relationship"
    )


class CurrentInventory(Base):
    """Table template for enterprise products inventory"""

    __tablename__ = "current_inventory"
    id = Column(Integer, primary_key=True, index=True)
    departments_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    created_at = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    product_in_stock = Column(Integer, nullable=False)
    product_to_come = Column(Integer, nullable=False)

    department_relationship = relationship(
        "Department", back_populates="inventory_relationship"
    )
    product_relationship = relationship(
        "Product", back_populates="inventory_relationship"
    )
    movement_relationship = relationship(
        "InventoryMovement", back_populates="current_inventory_relationship"
    )


class Product(Base):
    """Template for creation products names"""

    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    base_price = Column(Float, nullable=False)
    product_removed = Column(Boolean, default=False)
    inventory_relationship = relationship(
        "CurrentInventory", back_populates="product_relationship"
    )


class Card(Base):
    """Template for creation of cards"""

    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String, nullable=False, unique=True)
    card_status = Column(Boolean, default=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    issued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    user_card_relationship = relationship(
        "Employee", back_populates="card_relationship"
    )


class InventoryMovement(Base):
    """Table template for inventory movement"""

    __tablename__ = "inventory_movements"
    id = Column(Integer, primary_key=True, index=True)
    current_inventory_id = Column(
        Integer, ForeignKey("current_inventory.id"), nullable=False
    )
    movement_type = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price_at_transaction = Column(Float, nullable=False)
    timestamp = Column(
        DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    current_inventory_relationship = relationship(
        "CurrentInventory", back_populates="movement_relationship"
    )
