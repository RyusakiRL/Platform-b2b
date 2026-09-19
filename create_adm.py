"""Create a admnistrator for the system, to check any database"""

from getpass import getpass
from sqlalchemy.orm import Session
from models.workforce import Account, Employee
from models.enums import AccountRole
from schemas import AccountValidation
from security import generator_hash_password
from database import SESSIONLOCAL


def new_server_administrator(new_adm: AccountValidation, db_session: Session):
    """Create a new admnistrator in the system"""
    employee = db_session.get(Employee, new_adm.employee_id)

    if not employee or not employee.is_active:
        print("Active employee not found.")
        return
    adm_existence = (
        db_session.query(Account)
        .filter(Account.employee_id == new_adm.employee_id)
        .first()
    )
    if adm_existence:
        print("This id already exists input a other id")
        return
    if db_session.query(Account).filter(Account.username == new_adm.username).first():
        print("This username already exists input a other username")
        return

    hashed_password = generator_hash_password(new_adm.password)

    creation_of_new_administrator = Account(
        username=new_adm.username,
        password_hash=hashed_password,
        role=AccountRole.ADMINISTRATOR,
        employee_id=new_adm.employee_id,
    )

    db_session.add(creation_of_new_administrator)
    db_session.commit()
    db_session.refresh(creation_of_new_administrator)
    print("Sucess in administrator creation")


if __name__ == "__main__":
    username = input("Administrator username: ").strip().lower()
    password = getpass("Administrator password: ")
    employee_id = int(input("Employee ID: "))

    new_administrator = AccountValidation(
        username=username,
        password=password,
        employee_id=employee_id,
        role=AccountRole.ADMINISTRATOR,
    )

    with SESSIONLOCAL() as db:
        try:
            new_server_administrator(new_adm=new_administrator, db_session=db)
        except Exception:
            db.rollback()
            raise
