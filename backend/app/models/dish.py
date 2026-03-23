"""
菜品模型
"""
from sqlalchemy import Column, Integer, String, Float, JSON
from ..database import Base

class Dish(Base):
    __tablename__ = "dishes"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False, index=True)
    main_ingredients = Column(JSON, nullable=False) # list of str
    process_type = Column(String(100), nullable=False)
    flavor = Column(String(100), nullable=False)
    cost_per_serving = Column(Float, nullable=False)
    nutrition = Column(JSON, nullable=False) # dict: calories, protein, carbs, fat
    tags = Column(JSON, nullable=False) # list of str
