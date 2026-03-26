from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class DishBase(BaseModel):
    name: str = Field(..., description="菜品名称")
    category: str = Field(..., description="菜品分类")
    ingredients_quantified: List[Dict[str, Any]] = Field(default_factory=list, description="量化食材列表")
    applicable_meals: List[str] = Field(default_factory=list, description="适用餐次")
    flavor: str = Field(..., description="口味")
    cost_per_serving: float = Field(..., description="单份成本")
    nutrition: Dict[str, float] = Field(..., description="营养成分：热量、蛋白质、碳水、脂肪")
    tags: List[str] = Field(default_factory=list, description="标签列表")

class DishCreate(DishBase):
    pass

class DishUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    ingredients_quantified: Optional[List[Dict[str, Any]]] = None
    applicable_meals: Optional[List[str]] = None
    flavor: Optional[str] = None
    cost_per_serving: Optional[float] = None
    nutrition: Optional[Dict[str, float]] = None
    tags: Optional[List[str]] = None

class DishRead(DishBase):
    id: int

    class Config:
        from_attributes = True
