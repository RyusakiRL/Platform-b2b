"""Router for card management endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from schemas import CardValidation
from services.cards_service import card_creation, card_disable

router = APIRouter(prefix="/cards", tags=["Cards management"])


@router.post("/create")
def create_card(
    card_validation: CardValidation,
    login_confirmation: int,
    db: Session = Depends(get_db),
):
    """Endpoint to create a card for a user."""
    return card_creation(
        card_validation=card_validation, login_confirmation=login_confirmation, db=db
    )


@router.patch("/disable/{card_id}")
def disable_card(card_id: int, login_confirmation: int, db: Session = Depends(get_db)):
    """Endpoint to disable a card for a user."""
    return card_disable(card_id=card_id, login_confirmation=login_confirmation, db=db)
