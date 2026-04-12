from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.sql import func
import uuid

from .base import Base, TenantAwareMixin

class DifyConnector(Base, TenantAwareMixin):
    """Dify AI Platform Connector Configuration.
    
    Dify连接器表 - 存储与Dify AI平台的连接配置
    """
    __tablename__ = "ai_dify_connectors"
    __table_args__ = {"comment": "Dify AI平台连接器表"}

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()), comment="连接器ID")
    name = Column(String(100), nullable=False, comment="连接器名称")
    description = Column(String(255), nullable=True, comment="连接器描述")
    api_url = Column(String(255), nullable=False, comment="API地址(通常是 https://api.dify.ai/v1)")
    api_key = Column(String(255), nullable=False, comment="API密钥(考虑未来加密存储)")
    is_active = Column(Boolean, default=True, comment="是否激活")
    
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), comment="更新时间")
