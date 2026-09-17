"""Module responsible for security, encryption, and JWT token generation."""

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi.security import OAuth2PasswordBearer
from fastapi import Depends, HTTPException, status
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def generator_hash_password(password: str) -> str:
    """
    Receive the password in pure text and return ilegible Hash to save in database
    """
    return pwd_context.hash(password)


def verify_password(password_pure_text: str, hashed_password: str) -> bool:
    """
    Compare the password entered by the user during login with the hash stored in the database.
    Returns True if the password is correct, or False if it is incorrect.
    """
    return pwd_context.verify(password_pure_text, hashed_password)


def create_token_jwt(data: dict):
    """Generates the digital badge (JWT Token) for the user."""
    data_encoding = data.copy()

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    data_encoding.update({"exp": expiration})

    encoded_token = jwt.encode(data_encoding, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def verify_token(token: str = Depends(oauth2_scheme)):
    """Read the digital badge JWT and find your owner"""

    exception_not_authorized = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired badge",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:

        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        user_name: str = payload.get("sub")

        if user_name is None:
            raise exception_not_authorized

        return user_name

    except JWTError as original_error:

        raise exception_not_authorized from original_error
