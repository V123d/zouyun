"""
主副食、燃料定量标准模型
"""
from sqlalchemy import Column, Integer, String, JSON, Boolean
from ..database import Base


class StandardQuota(Base):
    __tablename__ = "standard_quotas"

    id = Column(Integer, primary_key=True, index=True)
    class_type = Column(String(50), nullable=False, unique=True, index=True)
    quotas = Column(JSON, nullable=False)
    is_system = Column(Boolean, default=False)
    name = Column(String(100), nullable=True, default="")
    description = Column(String(500), nullable=True, default="")
    quota_type = Column(String(20), nullable=True, default="ingredient")
