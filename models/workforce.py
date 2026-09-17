"""Models for the workforce management system."""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, ForeignKey
from sqlalchemy.orm import relationship
from models.base import Base
from models.enums import AccountRole


class Employee(Base):
    """Employee table template for creation of employees"""

    __tablename__ = "employees"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(100), nullable=False, index=True)
    phone = Column(String(20), nullable=True)
    address = Column(String(255), nullable=True)
    hired_at = Column(DateTime(timezone=True), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)

    account = relationship(
        "Account",
        back_populates="employee",
        uselist=False,
    )

    cards = relationship(
        "Card",
        back_populates="employee",
    )

    time_records = relationship(
        "TimeRecord",
        back_populates="employee",
    )

    payrolls = relationship(
        "MonthlyPayroll",
        back_populates="employee",
    )
    compensations = relationship("Compensation", back_populates="employee")
    managed_departments = relationship("Department", back_populates="manager")


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

    employee = relationship(
        "Employee",
        back_populates="account",
    )
    audit_logs = relationship("AuditLog", back_populates="account")
    inventory_movements = relationship("InventoryMovement", back_populates="account")


class Department(Base):
    """Template for Department creation"""

    __tablename__ = "departments"
    id = Column(Integer, primary_key=True, index=True)
    manager_employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    department_title = Column(String, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    manager = relationship("Employee", back_populates="managed_departments")


class Card(Base):
    """Template for creation of cards"""

    __tablename__ = "cards"
    id = Column(Integer, primary_key=True, index=True)
    card_number = Column(String, nullable=False, unique=True)
    is_active = Column(Boolean, default=True, nullable=False)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    issued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    disabled_at = Column(DateTime(timezone=True), nullable=True)
    employee = relationship("Employee", back_populates="cards")
