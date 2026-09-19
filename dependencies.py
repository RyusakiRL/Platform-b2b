"""Dependencies for FastAPI routes."""

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Account
from security import verify_token


def get_current_account(
    account_id: str = Depends(verify_token),
    db: Session = Depends(get_db),
) -> Account:
    """Retrieve the current account based on the provided account ID."""
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        parsed_id = int(account_id)
    except (TypeError, ValueError) as exc:
        raise credentials_error from exc

    account = db.get(Account, parsed_id)

    if not account or not account.is_active:
        raise credentials_error

    return account
