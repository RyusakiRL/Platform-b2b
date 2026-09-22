"""Router for card management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import CardValidation
from dependencies import get_current_account
from services.cards_service import card_creation, card_disable
from models.workforce import Account

router = APIRouter(prefix="/cards", tags=["Cards management"])


@router.post("/create")
def create_card(
    card_validation: CardValidation,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to create a card for a user."""
    return card_creation(
        card_validation=card_validation, current_account=current_account, db=db
    )


@router.patch("/disable/{card_id}")
def disable_card(
    card_id: int,
    current_account: Account = Depends(get_current_account),
    db: Session = Depends(get_db),
):
    """Endpoint to disable a card for a user."""
    return card_disable(card_id=card_id, current_account=current_account, db=db)
