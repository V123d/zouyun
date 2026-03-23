from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.sql import func
from ..database import Base

class MenuHistory(Base):
    __tablename__ = "menu_histories"

    id = Column(String(50), primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    name = Column(String(100))
    menu_data = Column(JSON)
    metrics_data = Column(JSON)
    config_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
