from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

from .base import Base, TenantAwareMixin

class DifyConnector(Base, TenantAwareMixin):
    __tablename__ = "dify_connectors"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    description = Column(String(255), nullable=True)
    api_url = Column(String(255), nullable=False)  # Usually https://api.dify.ai/v1
    api_key = Column(String(255), nullable=False)  # Consider encrypting this in future
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
