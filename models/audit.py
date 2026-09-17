"""Audit log models for the application"""

from datetime import datetime, timezone
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, JSON, ForeignKey, DateTime

from models.base import Base


class AuditLog(Base):
    """Table template for audit logs"""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey("accounts.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(100), nullable=False)
    entity_id = Column(String(100), nullable=True)
    old_values = Column(JSON, nullable=True)
    new_values = Column(JSON, nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    account = relationship("Account", back_populates="audit_logs")
