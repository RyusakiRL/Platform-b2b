"""Router for user-related endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import EmployeeValidation, AccountValidation
from models import Account
from dependencies import get_current_account
from services.users_service import (
    create_employee,
    create_manager,
    employee_demission,
    deactive_manager_account,
)

router = APIRouter(prefix="/users", tags=["User management"])


@router.post("/employee/create")
def create_employee_route(
    employee: EmployeeValidation,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to create an employee."""
    return create_employee(employee=employee, current_account=current_account, db=db)


@router.post("/manager/create")
def create_manager_route(
    manager: AccountValidation,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to create a manager."""
    return create_manager(
        current_account=current_account, db=db, account_validation=manager
    )


@router.post("/employee/demit")
def employee_demission_route(
    employee_id: int,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to demit an employee."""
    return employee_demission(
        employee_id=employee_id, current_account=current_account, db=db
    )


@router.post("/manager/{manager_id}/deactivate")
def manager_demission_route(
    manager_id: int,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to demit a manager."""
    return deactive_manager_account(
        manager_id=manager_id, current_account=current_account, db=db
    )
