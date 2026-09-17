"""General enumerations for the application."""

import enum


class AccountRole(enum.Enum):
    """Role for account acess levels"""

    ADMINISTRATOR = "administrator"
    MANAGER = "manager"


class PaymentType(enum.Enum):
    """Payment type for employee compensation"""

    HOURLY = "hourly"
    MONTHLY = "monthly"


class MovementType(enum.Enum):
    """Movement type for inventory"""

    IN = "in"
    OUT = "out"
