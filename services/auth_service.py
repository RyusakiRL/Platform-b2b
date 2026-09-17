"""Login service module for handling user authentication and token generation."""

from fastapi import HTTPException
from sqlalchemy.orm import Session
from starlette.status import HTTP_403_FORBIDDEN, HTTP_401_UNAUTHORIZED

from models.workforce import Account
from security import verify_password, create_token_jwt


def login(db: Session, username: str, password: str):
    """Login in system and return the token"""
    account = db.query(Account).filter(Account.username == username).first()
    if not account or not verify_password(password, account.password):
        raise HTTPException(
            status_code=HTTP_401_UNAUTHORIZED, detail="Invalid credential"
        )

    if not account.is_active:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Account is inactive"
        )

    token = create_token_jwt({"sub": str(account.id)})
    return {"access_token": token, "token_type": "bearer"}
