from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

from .base import Base

class Tenant(Base):
    """
    Root Multi-Tenant entity representing a distinct Organization or Enterprise.
    All logic is bounded by the context of a specific tenant instance.
    """
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    domain = Column(String(100), nullable=True, unique=True)
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
