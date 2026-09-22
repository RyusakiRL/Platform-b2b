"""Card service module for managing card creation."""

import uuid
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from fastapi import HTTPException
from starlette.status import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from models.workforce import Card, Account, Employee
from models.enums import AccountRole
from schemas import CardValidation


def card_creation(
    card_validation: CardValidation, current_account: Account, db: Session
):
    """Allow a manager to create a card"""
    if not current_account.is_active or current_account.role not in [
        AccountRole.MANAGER,
        AccountRole.ADMINISTRATOR,
    ]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Acess denied: only manager or administrator can create cards",
        )
    employee_validation = db.query(Employee).filter(
        Employee.id == card_validation.employee_id
    )
    if not employee_validation:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Employee not found")

    card_existence = (
        db.query(Card).filter(Card.employee_id == card_validation.employee_id).all()
    )
    for cards in card_existence:
        if cards.is_active:
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail="Employee already have a active card",
            )

    generated_card_number_qr_code = str(uuid.uuid4())
    new_card = Card(
        card_number=generated_card_number_qr_code,
        users_id=card_validation.users_id,
    )
    db.add(new_card)
    db.commit()
    db.refresh(new_card)
    return {
        "message": "Card created successfully.",
        "qr_code": generated_card_number_qr_code,
    }


def card_disable(card_id: int, current_account: Account, db: Session):
    """Allow a manager to disable a card"""
    if not current_account.is_active or current_account.role not in [
        AccountRole.MANAGER,
        AccountRole.ADMINISTRATOR,
    ]:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Only manager or administrator can desactive cards",
        )
    card = db.query(Card).filter(Card.id == card_id).first()
    if not card:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Card not found")
    card.is_active = False
    card.disabled_at = datetime.now(timezone.utc)
    db.commit()

    return {"message": "Card disabled successfully."}
