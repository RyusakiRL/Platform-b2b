"""Card service module for managing card creation."""

import uuid
from sqlalchemy.orm import Session
from fastapi import HTTPException
from models import User, Card, Status
from schemas import CardValidation


def card_creation(
    card_validation: CardValidation, db: Session
):
    """Allow a manager to create a card"""
    creator = db.query(User).filter(User).first()
    if not creator or creator.is_active is False:
        raise HTTPException(status_code=404, detail="User not found or inactive.")
    card_user = db.query(User).filter(User.id == card_validation.users_id).first()

    if not card_user or card_user.is_active is False:
        raise HTTPException(status_code=404, detail="User not found or inactive.")
    if card_user.role_user == Status.ADMINISTRATOR:
        raise HTTPException(
            status_code=403,
            detail="Access denied: cannot create cards for administrators.",
        )
    if creator.role_user != Status.MANAGER and card_user.role_user == Status.OPERATOR:
        raise HTTPException(
            status_code=403,
            detail="Access denied: managers can only create cards for operators.",
        )

    if (
        creator.role_user != Status.ADMINISTRATOR
        and card_user.role_user == Status.MANAGER
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied: administrators can only create cards for managers.",
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


def card_disable(card_id: int, login_confirmation: int, db: Session):
    """Allow a manager to disable a card"""
    creator = db.query(User).filter(User.my_number == login_confirmation).first()
    if not creator or creator.is_active is False:
        raise HTTPException(status_code=404, detail="User not found or inactive.")
    card = db.query(Card).filter(Card.id == card_id).first()

    if not card:
        raise HTTPException(status_code=404, detail="Card not found.")

    card_user = db.query(User).filter(User.id == card.users_id).first()

    if not card_user or card_user.is_active is False:
        raise HTTPException(status_code=404, detail="User not found or inactive.")

    if card_user.role_user == Status.ADMINISTRATOR:
        raise HTTPException(
            status_code=403,
            detail="Access denied: cannot disable cards for administrators.",
        )
    if creator.role_user != Status.MANAGER and card_user.role_user == Status.OPERATOR:
        raise HTTPException(
            status_code=403,
            detail="Access denied: managers can only disable cards for operators.",
        )

    if (
        creator.role_user != Status.ADMINISTRATOR
        and card_user.role_user == Status.MANAGER
    ):
        raise HTTPException(
            status_code=403,
            detail="Access denied: administrators can only disable cards for managers.",
        )

    card.card_status = False
    db.commit()

    return {"message": "Card disabled successfully."}
