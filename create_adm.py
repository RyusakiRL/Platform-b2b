"""Create an administrator and its employee in a single transaction."""

from datetime import datetime, timezone
from getpass import getpass

from pydantic import ValidationError
from sqlalchemy.orm import Session

from database import SESSIONLOCAL
from models.enums import AccountRole
from models.workforce import Account, Employee
from schemas import AccountValidation
from security import generator_hash_password


def new_server_administrator(
    username: str,
    password: str,
    db_session: Session,
) -> int:
    """Create the employee and administrator; return the account ID."""
    username = username.strip().lower()

    try:
        if len(password.encode("utf-8")) > 72:
            raise ValueError(
                "The password is too long. It must be at most 72 bytes when encoded in UTF-8."
            )

        username_exists = (
            db_session.query(Account).filter(Account.username == username).first()
        )

        if username_exists:
            raise ValueError("This username is already registered.")

        new_employee = Employee(
            full_name="Administrator",
            hired_at=datetime.now(timezone.utc),
            is_active=True,
        )

        db_session.add(new_employee)
        db_session.flush()

        new_adm = AccountValidation(
            username=username,
            password=password,
            employee_id=new_employee.id,
            role_user=AccountRole.ADMINISTRATOR,
        )

        new_account = Account(
            username=new_adm.username,
            password_hash=generator_hash_password(new_adm.password),
            role=AccountRole.ADMINISTRATOR,
            employee_id=new_employee.id,
            is_active=True,
        )

        db_session.add(new_account)
        db_session.flush()

        administrator_id = new_account.id

        db_session.commit()

        return administrator_id

    except Exception:
        db_session.rollback()
        raise


if __name__ == "__main__":
    administrator_username = input("Username of the administrator: ")
    administrator_password = getpass("Password of the administrator: ")

    with SESSIONLOCAL() as db:
        try:
            created_id = new_server_administrator(
                username=administrator_username,
                password=administrator_password,
                db_session=db,
            )

        except ValidationError as exc:
            print("Invalid data:")

            for error in exc.errors(include_input=False):
                field = ".".join(str(part) for part in error["loc"])
                print(f"- {field}: {error['msg']}")

        except ValueError as exc:
            print(f"Error: {exc}")

        else:
            print(f"Administrator created successfully! Account ID: {created_id}")
