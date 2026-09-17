"""Payroll models for the application"""

from sqlalchemy import (
    Column,
    Integer,
    DateTime,
    Enum,
    ForeignKey,
    Numeric,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from models.base import Base

from models.enums import PaymentType


class TimeRecord(Base):
    """Table template for time record creation"""

    __tablename__ = "time_records"
    id = Column(
        Integer,
        primary_key=True,
    )
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )

    clock_in = Column(DateTime(timezone=True), nullable=False)
    clock_out = Column(DateTime(timezone=True), nullable=True)
    hour_worked = Column(Numeric(8, 2), nullable=True)
    employee = relationship("Employee", back_populates="time_records")
    __table_args__ = (
        CheckConstraint(
            "clock_out is NULL OR clock_out > clock_in",
            name="ck_time_valid_period",
        ),
    )


class MonthlyPayroll(Base):
    """Table template for monthly payment"""

    __tablename__ = "monthly_payroll"
    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(
        Integer, ForeignKey("employees.id"), nullable=False, index=True
    )
    datetime_payment = Column(DateTime(timezone=True), nullable=True)
    base_salary = Column(Numeric(12, 2), nullable=False)
    overtime_pay = Column(Numeric(12, 2), nullable=False)
    tax_deductions = Column(Numeric(12, 2), nullable=False)
    reference_year = Column(Integer, nullable=False)
    reference_month = Column(Integer, nullable=False)
    employee = relationship("Employee", back_populates="payrolls")
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "reference_year",
            "reference_month",
            name="uq_payroll_employee_period",
        ),
        CheckConstraint(
            "reference_month BETWEEN 1 AND 12",
            name="ck_payroll_valid_month",
        ),
        CheckConstraint(
            "base_salary >= 0",
            name="ck_payroll_base_salary_nonnegative",
        ),
        CheckConstraint(
            "overtime_pay >= 0",
            name="ck_payroll_overtime_nonnegative",
        ),
        CheckConstraint(
            "tax_deductions >= 0",
            name="ck_payroll_deductions_nonnegative",
        ),
        UniqueConstraint(
            "employee_id",
            "reference_year",
            "reference_month",
            name="uq_payroll_employee_period",
        ),
    )


class Compensation(Base):
    """Table template for employee compensation"""

    __tablename__ = "compensations"

    id = Column(Integer, primary_key=True)

    employee_id = Column(
        Integer,
        ForeignKey("employees.id"),
        nullable=False,
        index=True,
    )

    payment_type = Column(Enum(PaymentType), nullable=False)
    amount = Column(Numeric(12, 2), nullable=False)
    valid_from = Column(DateTime(timezone=True), nullable=False)
    valid_until = Column(DateTime(timezone=True), nullable=True)
    employee = relationship("Employee", back_populates="compensations")
    __table_args__ = (
        CheckConstraint(
            "amount >= 0",
            name="ck_compensation_amount_nonnegative",
        ),
        CheckConstraint(
            "valid_until IS NULL OR valid_until > valid_from",
            name="ck_compensation_valid_period",
        ),
    )
