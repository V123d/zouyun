from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update, delete
from ..services.data_enrichment import search_dishes
from ..database import AsyncSessionLocal
from ..models.dish import Dish
from ..schemas.dish_schema import DishCreate, DishUpdate, DishRead
from typing import List
import json
import os

router = APIRouter(prefix="/api/dishes", tags=["菜品库"])

# 自定义分类缓存（菜品分类 + 配料分类）
# 存储在 app 目录下的配置文件中
CUSTOM_CATEGORIES_FILE = os.path.join(os.path.dirname(__file__), "..", "custom_categories.json")

def _load_custom_categories() -> dict:
    """加载自定义分类配置"""
    if os.path.exists(CUSTOM_CATEGORIES_FILE):
        try:
            with open(CUSTOM_CATEGORIES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {"dish_categories": []}

def _save_custom_categories(data: dict):
    """保存自定义分类配置"""
    with open(CUSTOM_CATEGORIES_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

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
    """获取菜品库中所有不重复的分类列表（含自定义分类）"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Dish.category).distinct())
        db_categories = [row[0] for row in result.all() if row[0]]

    # 合并自定义分类
    custom_data = _load_custom_categories()
    all_categories = sorted(set(db_categories + custom_data.get("dish_categories", [])))
    return all_categories


@router.post("/categories", status_code=status.HTTP_201_CREATED)
async def add_category(category_type: str, category_name: str):
    """
    添加新的菜品分类
    - category_type: "dish"
    - category_name: 新分类名称
    """
    if category_type not in ("dish",):
        raise HTTPException(status_code=400, detail="category_type 必须是 'dish'")

    if not category_name or not category_name.strip():
        raise HTTPException(status_code=400, detail="分类名称不能为空")

    category_name = category_name.strip()

    custom_data = _load_custom_categories()
    key = "dish_categories"

    if category_name not in custom_data[key]:
        custom_data[key].append(category_name)
        _save_custom_categories(custom_data)

    return {"success": True, "type": category_type, "name": category_name}

def _extract_and_save_categories(dish_data: dict):
    """
    从菜品数据中提取菜品分类，自动保存到自定义分类文件中。
    """
    custom_data = _load_custom_categories()

    # 提取菜品分类
    dish_category = dish_data.get("category")
    if dish_category and dish_category.strip():
        dish_category = dish_category.strip()
        if dish_category not in custom_data["dish_categories"]:
            custom_data["dish_categories"].append(dish_category)

    _save_custom_categories(custom_data)


@router.post("/", response_model=DishRead, status_code=status.HTTP_201_CREATED)
async def create_dish(dish_in: DishCreate):
    """创建新菜品"""
    dish_dict = dish_in.dict()
    # 自动提取并保存分类
    _extract_and_save_categories(dish_dict)

    async with AsyncSessionLocal() as session:
        new_dish = Dish(**dish_dict)
        session.add(new_dish)
        await session.commit()
        await session.refresh(new_dish)
        return new_dish


@router.put("/{dish_id}", response_model=DishRead)
async def update_dish(dish_id: int, dish_in: DishUpdate):
    """更新指定菜品"""
    update_data = dish_in.dict(exclude_unset=True)
    # 自动提取并保存分类
    _extract_and_save_categories(update_data)

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Dish).where(Dish.id == dish_id))
        dish = result.scalar_one_or_none()
        if not dish:
            raise HTTPException(status_code=404, detail="Dish not found")

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
