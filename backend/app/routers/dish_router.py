from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete
from ..services.data_enrichment import search_dishes
from ..database import AsyncSessionLocal
from ..models.dish import Dish
from ..schemas.dish_schema import DishCreate, DishUpdate, DishRead
from typing import List

router = APIRouter(prefix="/api/dishes", tags=["菜品库"])

@router.get("/search", response_model=List[DishRead])
async def dishes_search(q: str = ""):
    """搜索菜品库"""
    if not q.strip():
        return []
    return await search_dishes(q.strip())

@router.get("/library", response_model=List[DishRead])
async def dishes_library():
    """获取完整菜品库"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Dish))
        return result.scalars().all()

@router.get("/categories")
async def dishes_categories():
    """获取菜品库中所有不重复的分类列表"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Dish.category).distinct())
        categories = [row[0] for row in result.all() if row[0]]
        return sorted(categories)

@router.post("/", response_model=DishRead, status_code=status.HTTP_201_CREATED)
async def create_dish(dish_in: DishCreate):
    """创建新菜品"""
    async with AsyncSessionLocal() as session:
        new_dish = Dish(**dish_in.dict())
        session.add(new_dish)
        await session.commit()
        await session.refresh(new_dish)
        return new_dish

@router.put("/{dish_id}", response_model=DishRead)
async def update_dish(dish_id: int, dish_in: DishUpdate):
    """更新指定菜品"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Dish).where(Dish.id == dish_id))
        dish = result.scalar_one_or_none()
        if not dish:
            raise HTTPException(status_code=404, detail="Dish not found")
        
        update_data = dish_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(dish, key, value)
        
        session.add(dish)
        await session.commit()
        await session.refresh(dish)
        return dish

@router.delete("/{dish_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dish(dish_id: int):
    """删除指定菜品"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Dish).where(Dish.id == dish_id))
        dish = result.scalar_one_or_none()
        if not dish:
            raise HTTPException(status_code=404, detail="Dish not found")
        
        await session.delete(dish)
        await session.commit()
        return None
