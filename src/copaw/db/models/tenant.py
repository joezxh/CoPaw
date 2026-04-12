from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

from .base import Base

class Tenant(Base):
    """
    Root Multi-Tenant entity representing a distinct Organization or Enterprise.
    All logic is bounded by the context of a specific tenant instance.
    
    租户表 - 根多租户实体,代表独立的组织或企业
    所有逻辑都限定在特定租户实例的上下文中
    """
    __tablename__ = "sys_tenants"
    __table_args__ = {"comment": "租户表"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="租户ID")
    name = Column(String(100), nullable=False, comment="租户名称")
    domain = Column(String(100), nullable=True, unique=True, comment="租户域名标识")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
