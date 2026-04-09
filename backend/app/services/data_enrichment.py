"""
走云智能排菜系统 — 数据补全智能体

职责：将 LLM 返回的紧凑格式菜单（仅 {id, name}）补全为包含完整属性的菜品数据。
"""
import logging
from typing import Any

from sqlalchemy import select

from .base_agent import BaseAgent
from ..database import AsyncSessionLocal
from ..models.dish import Dish

logger = logging.getLogger(__name__)

__all__ = ["DataEnrichmentAgent", "search_dishes"]


def _normalize_dish_id(raw: Any) -> int | None:
    """
    将 LLM/JSON 中的 id 统一为 int。
    常见坑：163.0（float）、\"163\"（str）在 Python 中无法与 dish_index 的 int 键匹配，
    会导致整桌菜全部走降级分支（口味等为空 → 前端显示「未知」）。
    """
    if raw is None or isinstance(raw, bool):
        return None
    try:
        i = int(float(raw))
        return i if i > 0 else None
    except (TypeError, ValueError):
        return None


def _dish_row_dict(d: Dish) -> dict[str, Any]:
    return {
        "id": d.id,
        "name": d.name,
        "category": d.category,
        "ingredients_quantified": d.ingredients_quantified,
        "applicable_meals": d.applicable_meals,
        "flavor": d.flavor,
        "cost_per_serving": d.cost_per_serving,
        "nutrition": d.nutrition,
        "tags": d.tags,
    }


class DataEnrichmentAgent(BaseAgent):
    """数据补全智能体（纯 Python，不调用 LLM）"""

    agent_id = "data-enrichment"
    agent_name = "Data Enrichment / 数据补全智能体"
    agent_description = "将 AI 生成的紧凑菜单（仅含菜品 ID 和名称）补全为包含食材、营养、成本等完整属性的菜品数据"
    agent_type = "rule"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        menu: dict = kwargs.get("menu", {})
        enriched_menu = await _enrich_menu_data(menu)
        return {"success": True, "menu": enriched_menu}


async def _enrich_menu_data(menu: dict) -> dict:
    """
    将 LLM 返回的紧凑格式补全为前端需要的完整菜品数据（异步从数据库查询）。
    """
    normalized_ids: set[int] = set()
    for date, meals in menu.items():
        for meal_name, categories in meals.items():
            for cat_name, dishes in categories.items():
                for dish in dishes:
                    nid = _normalize_dish_id(dish.get("id"))
                    if nid is not None:
                        normalized_ids.add(nid)

    dish_index: dict[int, dict[str, Any]] = {}
    if normalized_ids:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Dish).where(Dish.id.in_(list(normalized_ids))))
            for d in result.scalars().all():
                dish_index[d.id] = _dish_row_dict(d)

    # 按菜名二次补全：id 缺失、类型不匹配或幻觉 id 时，仍可用名称命中库内菜品
    names_needed: set[str] = set()
    for date, meals in menu.items():
        for meal_name, categories in meals.items():
            for cat_name, dishes in categories.items():
                for dish in dishes:
                    nid = _normalize_dish_id(dish.get("id"))
                    name = (dish.get("name") or "").strip()
                    if not name:
                        continue
                    if nid is None or nid not in dish_index:
                        names_needed.add(name)

    name_index: dict[str, dict[str, Any]] = {}
    if names_needed:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Dish).where(Dish.name.in_(list(names_needed))))
            for d in result.scalars().all():
                if d.name not in name_index:
                    name_index[d.name] = _dish_row_dict(d)

    enriched: dict = {}
    for date, meals in menu.items():
        enriched[date] = {}
        for meal_name, categories in meals.items():
            enriched[date][meal_name] = {}
            for cat_name, dishes in categories.items():
                enriched_dishes = []
                for dish in dishes:
                    nid = _normalize_dish_id(dish.get("id"))
                    name = (dish.get("name") or "").strip()

                    picked: dict[str, Any] | None = None
                    if nid is not None and nid in dish_index:
                        picked = dish_index[nid]
                    elif name and name in name_index:
                        picked = name_index[name]

                    if picked:
                        enriched_dishes.append(dict(picked))
                    else:
                        logger.warning(
                            "数据补全未命中: id=%s name=%s category=%s",
                            dish.get("id"),
                            name or dish.get("name"),
                            cat_name,
                        )
                        enriched_dishes.append({
                            "id": nid or 0,
                            "name": name or dish.get("name", "未知菜品"),
                            "category": cat_name,
                            "ingredients_quantified": dish.get("ingredients_quantified", []),
                            "applicable_meals": dish.get("applicable_meals", []),
                            "flavor": dish.get("flavor", ""),
                            "cost_per_serving": dish.get("cost_per_serving", 0),
                            "nutrition": dish.get("nutrition", {
                                "calories": 0, "protein": 0, "carbs": 0, "fat": 0,
                            }),
                            "tags": dish.get("tags", []),
                        })
                enriched[date][meal_name][cat_name] = enriched_dishes
    return enriched


async def search_dishes(query: str) -> list[dict[str, Any]]:
    """搜索菜品库（数据库实现）。"""
    query_lower = query.lower()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Dish).where(
                Dish.name.ilike(f"%{query_lower}%") |
                Dish.category.ilike(f"%{query_lower}%")
            ).limit(20)
        )
        dishes = result.scalars().all()

        return [_dish_row_dict(d) for d in dishes]
