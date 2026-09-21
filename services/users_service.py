"""General user service module for managing user creation and demission."""

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_400_BAD_REQUEST,
    HTTP_404_NOT_FOUND,
)
from models.workforce import Employee, Account
from models.enums import AccountRole
from schemas import EmployeeValidation, AccountValidation
from security import generator_hash_password


def create_employee(
    employee: EmployeeValidation, current_account: Account, db: Session
):
    """Allow a manager to create a employee"""
    if not current_account.is_active or current_account.role not in [
        AccountRole.MANAGER,
        AccountRole.ADMINISTRATOR,
    ]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only activemanager or administrator can create employees.",
        )
    new_employee = Employee(
        full_name=employee.full_name,
        phone=employee.phone,
        address=employee.address,
        hired_at=employee.hired_at,
    )
    db.add(new_employee)
    db.commit()
    db.refresh(new_employee)
    return {"message": "Welcome to our enterprise."}


def create_manager(
    current_account: Account, db: Session, account_validation: AccountValidation
):
    """Create a security manager route: manage works, progress and others functions"""
    if current_account.role != AccountRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only administrator can create managers.",
        )
    employee_existence = (
        db.query(Employee).filter(Employee.id == account_validation.employee_id).first()
    )
    if not employee_existence or employee_existence.is_active is False:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail="Active employee not found.",
        )
    manager_existence = (
        db.query(Account)
        .filter(Account.employee_id == account_validation.employee_id)
        .first()
    )
    if manager_existence:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="This employee already has an account.",
        )
    username_exists = (
        db.query(Account)
        .filter(Account.username == account_validation.username)
        .first()
    )

    if username_exists:
        raise HTTPException(
            status_code=409,
            detail="Username already exists.",
        )
    new_manager = Account(
        username=account_validation.username,
        password_hash=generator_hash_password(account_validation.password),
        role=AccountRole.MANAGER,
        employee_id=account_validation.employee_id,
    )

    db.add(new_manager)
    db.commit()
    db.refresh(new_manager)
    return {"message": "Welcome to the new manager"}


def employee_demission(db: Session, employee_id: int, current_account: Account):
    """Allow a manager to demission a employee"""
    if current_account.role != AccountRole.MANAGER or not current_account.is_active:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only active manager can demission employees.",
        )
    account_existence = (
        db.query(Account).filter(Account.employee_id == employee_id).first()
    )
    employee_existence = db.query(Employee).filter(Employee.id == employee_id).first()
    if not employee_existence or employee_existence.is_active is False:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Employee not found")

    if account_existence and account_existence.is_active:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="Cannot demission employee with an active account.",
        )

    disabled_at = datetime.now(timezone.utc)

    for card in employee_existence.cards:
        if card.is_active:
            card.is_active = False
            card.disabled_at = disabled_at

    employee_existence.is_active = False

    db.commit()
    db.refresh(employee_existence)
    return {"message": "Employee demissioned successfully."}


def deactive_manager_account(db: Session, current_account: Account, manager_id: int):
    """Allow a administrator to deactivate a manager"""
    if current_account.role != AccountRole.ADMINISTRATOR:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Access denied: only administrator can deactivate managers.",
        )
    manager_existence = db.query(Account).filter(Account.id == manager_id).first()
    if not manager_existence or manager_existence.is_active is False:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Manager not found")
    if manager_existence.role != AccountRole.MANAGER:
        raise HTTPException(
            status_code=HTTP_400_BAD_REQUEST,
            detail="The account is not a manager.",
        )
    manager_existence.is_active = False
    db.commit()
    db.refresh(manager_existence)
    return {"message": "Manager account deactivated successfully."}
