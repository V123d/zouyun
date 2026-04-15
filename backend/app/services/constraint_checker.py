"""
走云智能排菜系统 — 约束校验智能体
"""
import logging
from collections import defaultdict
from datetime import date as date_cls
from typing import Any
from sqlalchemy import select

from .base_agent import BaseAgent
from ..database import AsyncSessionLocal
from ..models.dish import Dish
from ..schemas.chat_schema import ConstraintAlert

logger = logging.getLogger(__name__)


def _get_main_ingredient(dish_record: dict | Any) -> str | None:
    """从菜品记录中提取主配料（amount_g 最大的那条配料）"""
    if hasattr(dish_record, 'ingredients_quantified'):
        ingredients = dish_record.ingredients_quantified
    elif isinstance(dish_record, dict):
        ingredients = dish_record.get('ingredients_quantified', [])
    else:
        return None
    ingredients = ingredients or []
    if not ingredients:
        return None
    best = None
    best_amt = -1.0
    for ing in ingredients:
        amt = float(ing.get('amount_g') or ing.get('amount') or ing.get('value') or 0)
        if amt > best_amt:
            best_amt = amt
            best = ing.get('name')
    return best


class ConstraintCheckerAgent(BaseAgent):
    """约束校验智能体（纯规则引擎，不调用 LLM）"""

    agent_id = "constraint-checker"
    agent_name = "Constraint Checker / 约束校验智能体"
    agent_description = "对生成的菜单进行确定性规则校验"
    agent_type = "rule"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        menu: dict = kwargs.get("menu", {})
        config: Any = kwargs.get("config", {})
        return await _check_menu(menu, config)


async def _check_menu(menu: dict, config: Any, daily_configs: dict = None) -> dict[str, Any]:
    alerts: list[dict] = []
    total_cost_raw = 0.0
    total_dishes = 0
    dish_name_counter: dict[str, int] = {}
    nutrition_scores: list[float] = []

    if isinstance(config, dict):
        ghc = config.get("global_hard_constraints", {})
        red_lines: set[str] = set(ghc.get("red_lines", []))
        meals_config_list: list[dict] = config.get("meals_config", [])
    else:
        red_lines = set(config.global_hard_constraints.red_lines)
        meals_config_list = [m.model_dump() for m in config.meals_config]

    meal_budgets: dict[str, float] = {}
    meal_diners: dict[str, int] = {}
    meal_structures: dict[str, dict[str, int]] = {}

    for mc in meals_config_list:
        if mc.get("enabled", True):
            meal_name = mc["meal_name"]
            meal_budgets[meal_name] = mc.get("budget_per_person", 999.0)
            meal_diners[meal_name] = mc.get("diners_count", 1)
            meal_structures[meal_name] = {
                cat["name"]: cat["count"]
                for cat in mc.get("dish_structure", {}).get("categories", [])
            }

    # 允许重复的分类（不触发跨天重复约束）
    ALLOW_REPEAT_CATEGORIES: set[str] = {"汤", "汤羹类", "主食", "面点类", "面食类", "米饭", "面食"}
    # 隔天一次的分类（不需要5天间隔，但仍参与主配料去重）
    EVERY_OTHER_DAY_CATEGORIES: set[str] = {"素菜"}
    cross_day_tracker: dict[tuple[str, str], list[str]] = {}

    # 抽取涉及的菜品 ID
    dish_ids = set()
    for date, meals in menu.items():
        for cat_dishes in meals.values():
            for dishes in cat_dishes.values():
                for dish in dishes:
                    if dish.get("id"):
                        dish_ids.add(dish["id"])

    dish_index = {}
    standard_quotas_dict = {}
    total_person_days = 0

    if dish_ids:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Dish).where(Dish.id.in_(list(dish_ids))))
            for d in result.scalars().all():
                dish_index[d.id] = d.__dict__

            from ..models.standard_quota import StandardQuota
            kitchen_class = "幼儿园大班"
            quota_profile_id = 1
            if isinstance(config, dict):
                kitchen_class = config.get("context_overview", {}).get("kitchen_class", "幼儿园大班")
                quota_profile_id = config.get("context_overview", {}).get("quota_profile_id", 1)
            else:
                kitchen_class = config.context_overview.kitchen_class
                quota_profile_id = config.context_overview.quota_profile_id

            sq_res = await session.execute(select(StandardQuota).where(StandardQuota.id == quota_profile_id))
            sq = sq_res.scalar_one_or_none()
            if not sq:
                sq_res = await session.execute(select(StandardQuota).where(StandardQuota.class_type == kitchen_class))
                sq = sq_res.scalar_one_or_none()
            if sq:
                standard_quotas_dict = sq.quotas

    for date, meals in menu.items():
        daily_dish_names: set[str] = set()

        if daily_configs and date in daily_configs:
            d_conf = daily_configs[date]
            d_list = d_conf.get("meals_config", []) if isinstance(d_conf, dict) else [m.model_dump() for m in d_conf.meals_config]
            d_meal_structures = {mc["meal_name"]: {c["name"]: c["count"] for c in mc.get("dish_structure", {}).get("categories", [])} for mc in d_list if mc.get("enabled", True)}
            d_meal_budgets = {mc["meal_name"]: mc.get("budget_per_person", 999.0) for mc in d_list if mc.get("enabled", True)}
            d_meal_diners = {mc["meal_name"]: mc.get("diners_count", 1) for mc in d_list if mc.get("enabled", True)}
        else:
            d_meal_structures = meal_structures
            d_meal_budgets = meal_budgets
            d_meal_diners = meal_diners

        daily_diners = max(d_meal_diners.values()) if d_meal_diners else 1
        total_person_days += daily_diners

        for meal_name, categories in meals.items():
            meal_cost_per_person = 0.0
            diners = d_meal_diners.get(meal_name, 1)
            budget = d_meal_budgets.get(meal_name, 999.0)

            for cat_name, dishes in categories.items():
                expected = d_meal_structures.get(meal_name, {}).get(cat_name)
                if expected is not None and len(dishes) != expected:
                    alerts.append(ConstraintAlert(
                        type="COUNT_MISMATCH",
                        date=date,
                        meal_name=meal_name,
                        category=cat_name,
                        detail=f"期望 {expected} 道，实际 {len(dishes)} 道"
                    ).model_dump())

                for dish in dishes:
                    dish_id = dish.get("id")
                    dish_name = dish.get("name", "未知")
                    total_dishes += 1

                    full = dish_index.get(dish_id, dish) if dish_id else dish
                    quantified = full.get("ingredients_quantified", [])
                    ingredients: list[str] = [i.get("name") for i in quantified if isinstance(i, dict)]
                    cost: float = float(full.get("cost_per_serving", 0))

                    for ingredient in ingredients:
                        if ingredient in red_lines:
                            alerts.append(ConstraintAlert(
                                type="RED_LINE",
                                date=date,
                                meal_name=meal_name,
                                category=cat_name,
                                dish_name=dish_name,
                                detail=f"含禁用食材「{ingredient}」"
                            ).model_dump())

                    meal_cost_per_person += cost * 0.4
                    total_cost_raw += cost * 0.4

                    if cat_name not in ALLOW_REPEAT_CATEGORIES:
                        dish_name_counter[dish_name] = dish_name_counter.get(dish_name, 0) + 1

                    if cat_name not in ALLOW_REPEAT_CATEGORIES:
                        if dish_name in daily_dish_names:
                            alerts.append(ConstraintAlert(
                                type="CROSS_MEAL_DUPLICATE",
                                date=date,
                                meal_name=meal_name,
                                category=cat_name,
                                dish_name=dish_name,
                                detail="在多个餐次中重复出现"
                            ).model_dump())
                        daily_dish_names.add(dish_name)

                    if cat_name not in ALLOW_REPEAT_CATEGORIES:
                        cross_day_tracker.setdefault((dish_name, cat_name), []).append(date)

                    nutrition = full.get("nutrition", {})
                    calories = float(nutrition.get("calories", 0))
                    if calories > 0:
                        score = min(100.0, max(0.0, 100.0 - abs(calories - 300) / 3.0))
                        nutrition_scores.append(score)

            if meal_cost_per_person > budget * 1.05:
                alerts.append(ConstraintAlert(
                    type="BUDGET_OVERFLOW",
                    date=date,
                    meal_name=meal_name,
                    detail=f"单人成本 ¥{meal_cost_per_person:.1f}，餐标 ¥{budget:.1f}，超出 {(meal_cost_per_person/budget - 1)*100:.0f}%"
                ).model_dump())

    for (dish_name, cat_name), dates in cross_day_tracker.items():
        if len(dates) > 1:
            sorted_dates = sorted(list(set(dates)))
            if cat_name in EVERY_OTHER_DAY_CATEGORIES:
                for i in range(1, len(sorted_dates)):
                    d1 = date_cls.fromisoformat(sorted_dates[i-1])
                    d2 = date_cls.fromisoformat(sorted_dates[i])
                    if (d2 - d1).days <= 1:
                        alerts.append(ConstraintAlert(
                            type="CROSS_DAY_DUPLICATE",
                            date=sorted_dates[i],
                            meal_name="",
                            dish_name=dish_name,
                            detail=f"「{cat_name}」连续两天重复出现 ({sorted_dates[i-1]} 和 {sorted_dates[i]})"
                        ).model_dump())
                        break
            else:
                for i in range(1, len(sorted_dates)):
                    d1 = date_cls.fromisoformat(sorted_dates[i-1])
                    d2 = date_cls.fromisoformat(sorted_dates[i])
                    if (d2 - d1).days < 5:
                        alerts.append(ConstraintAlert(
                            type="CROSS_DAY_DUPLICATE",
                            date=sorted_dates[i],
                            meal_name="",
                            dish_name=dish_name,
                            detail=f"「{cat_name}」在 {sorted_dates[i-1]} 和 {sorted_dates[i]} 间隔过近重复出现（要求间隔至少5天）"
                        ).model_dump())
                        break

    # ── 主配料重复校验 ────────────────────────────────────────────
    main_ingredient_tracker: dict[tuple[str, str], list[str]] = defaultdict(list)
    dish_index_by_name: dict[str, Any] = {}
    if dish_index:
        for dish_id, dish_record in dish_index.items():
            name = getattr(dish_record, 'name', None) or dish_record.get('name', '')
            if name:
                dish_index_by_name[name] = dish_record

    for (dish_name, cat_name), dates in cross_day_tracker.items():
        if cat_name in ALLOW_REPEAT_CATEGORIES:
            continue
        dish_record = dish_index_by_name.get(dish_name)
        if dish_record:
            main_ing = _get_main_ingredient(dish_record)
            if main_ing:
                key = (main_ing, cat_name)
                main_ingredient_tracker[key].extend(dates)

    # 同分类下主配料在 5 天内出现即告警（兜底防御）
    for (main_ing, cat_name), dates in main_ingredient_tracker.items():
        unique_dates = sorted(set(dates))
        for i in range(1, len(unique_dates)):
            d1 = date_cls.fromisoformat(unique_dates[i - 1])
            d2 = date_cls.fromisoformat(unique_dates[i])
            if (d2 - d1).days < 5:
                alerts.append(ConstraintAlert(
                    type="MAIN_INGREDIENT_REPEAT",
                    date=unique_dates[i],
                    meal_name="",
                    category=cat_name,
                    dish_name=main_ing,
                    detail=f"「{cat_name}」主配料「{main_ing}」在 {unique_dates[i-1]} 和 {unique_dates[i]} 间隔不足5天重复出现",
                ).model_dump())
                break

    total_non_exempt = sum(dish_name_counter.values())
    unique_count = len(dish_name_counter)
    repeat_rate = round((total_non_exempt - unique_count) / total_non_exempt * 100, 1) if total_non_exempt > 0 else 0.0

    MAX_REPEAT_RATE = 30.0
    if repeat_rate > MAX_REPEAT_RATE:
        alerts.append(ConstraintAlert(
            type="HIGH_REPEAT_RATE",
            date="全局",
            meal_name="",
            detail=f"菜品重复率 {repeat_rate}% 超过阈值 {MAX_REPEAT_RATE}%"
        ).model_dump())

    total_cost = _calc_total_cost(menu, meal_diners, daily_configs, dish_index)
    avg_nutrition = round(sum(nutrition_scores) / len(nutrition_scores), 1) if nutrition_scores else 0.0

    quota_compliance = []
    quota_type = getattr(sq, 'quota_type', None) or "nutrition"

    if standard_quotas_dict and total_person_days > 0:
        nutrition_keys = ["calories", "protein", "fat", "carbs"]
        nutrition_totals: dict[str, float] = {k: 0.0 for k in nutrition_keys}
        nutrition_name_map = {
            "calories": "卡路里",
            "protein": "蛋白质",
            "fat": "脂肪",
            "carbs": "碳水化合物",
        }
        nutrition_unit_map = {
            "calories": "kcal",
            "protein": "g",
            "fat": "g",
            "carbs": "g",
        }

        for date, meals in menu.items():
            if daily_configs and date in daily_configs:
                d_conf = daily_configs[date]
                d_list = d_conf.get("meals_config", []) if isinstance(d_conf, dict) else [m.model_dump() for m in d_conf.meals_config]
                d_meal_diners = {mc["meal_name"]: mc.get("diners_count", 1) for mc in d_list if mc.get("enabled", True)}
            else:
                d_meal_diners = meal_diners

            for meal_name, categories in meals.items():
                diners = d_meal_diners.get(meal_name, 1)
                for cat_name, dishes in categories.items():
                    for dish in dishes:
                        dish_id = dish.get("id")
                        full = dish_index.get(dish_id, dish) if dish_id else dish
                        nutrition = full.get("nutrition", {})
                        servings = float(dish.get("quantity") or 1) * diners
                        for key in nutrition_keys:
                            nutrition_totals[key] += float(nutrition.get(key, 0)) * servings

        for key in nutrition_keys:
            std_val = float(standard_quotas_dict.get(key, 0))
            if std_val > 0:
                actual_per_person_day = nutrition_totals[key] / total_person_days if total_person_days > 0 else 0
                rate = actual_per_person_day / std_val
                quota_compliance.append({
                    "name": nutrition_name_map[key],
                    "actual": round(actual_per_person_day, 1),
                    "standard": round(std_val, 1),
                    "rate": round(rate, 2),
                    "unit": nutrition_unit_map[key],
                })

    return {
        "success": True,
        "passed": len(alerts) == 0,
        "alerts": alerts,
        "quota_type": quota_type,
        "metrics": {
            "total_cost": round(total_cost, 2),
            "avg_nutrition_score": avg_nutrition,
            "repeat_rate": repeat_rate,
            "alert_count": len(alerts),
            "total_dishes": total_dishes,
            "unique_dishes": unique_count,
            "quota_compliance": quota_compliance,
        },
    }

def _calc_total_cost(menu: dict, meal_diners: dict[str, int], daily_configs: dict, dish_index: dict) -> float:
    total = 0.0
    for date, meals in menu.items():
        if daily_configs and date in daily_configs:
            d_conf = daily_configs[date]
            d_list = d_conf.get("meals_config", []) if isinstance(d_conf, dict) else [m.model_dump() for m in d_conf.meals_config]
            d_meal_diners = {mc["meal_name"]: mc.get("diners_count", 1) for mc in d_list if mc.get("enabled", True)}
        else:
            d_meal_diners = meal_diners

        for meal_name, categories in meals.items():
            diners = d_meal_diners.get(meal_name, 1)
            for cat_name, dishes in categories.items():
                for dish in dishes:
                    dish_id = dish.get("id")
                    full = dish_index.get(dish_id, dish) if dish_id else dish
                    cost = float(full.get("cost_per_serving", 0))
                    total += cost * diners * 0.4
    return total


async def _check_daily_nutrition(
    day_menu: dict,
    config_dict: dict,
    date_str: str,
) -> dict:
    """
    单天维度的灶别营养配额达标校验。

    为什么逐天校验而非全局校验：
    等所有天生成完再检查营养达标过晚，无法在生成过程中及时修正。
    逐天校验可以在每天生成后立即检查，不达标时触发重试。
    """
    alerts: list[dict] = []

    meals_config_list = config_dict.get("meals_config", [])
    meal_diners: dict[str, int] = {}
    for mc in meals_config_list:
        if mc.get("enabled", True):
            meal_diners[mc["meal_name"]] = mc.get("diners_count", 1)

    dish_ids = set()
    for categories in day_menu.values():
        for dishes in categories.values():
            for dish in dishes:
                if dish.get("id"):
                    dish_ids.add(dish["id"])

    dish_index: dict = {}
    standard_quotas_dict: dict = {}
    quota_type: str = "nutrition"

    if dish_ids:
        async with AsyncSessionLocal() as session:
            result = await session.execute(select(Dish).where(Dish.id.in_(list(dish_ids))))
            for d in result.scalars().all():
                dish_index[d.id] = d.__dict__

            from ..models.standard_quota import StandardQuota
            quota_profile_id = config_dict.get("context_overview", {}).get("quota_profile_id", 1)
            kitchen_class = config_dict.get("context_overview", {}).get("kitchen_class", "幼儿园大班")
            sq_res = await session.execute(select(StandardQuota).where(StandardQuota.id == quota_profile_id))
            sq = sq_res.scalar_one_or_none()
            if not sq:
                sq_res = await session.execute(select(StandardQuota).where(StandardQuota.class_type == kitchen_class))
                sq = sq_res.scalar_one_or_none()
            if sq:
                standard_quotas_dict = sq.quotas
                quota_type = getattr(sq, "quota_type", "nutrition")

    if not standard_quotas_dict:
        return {"passed": True, "alerts": [], "quota_compliance": [], "quota_type": quota_type}

    quota_compliance: list[dict] = []

    daily_diners = max(meal_diners.values()) if meal_diners else 1
    nutrition_keys = ["calories", "protein", "fat", "carbs"]
    nutrition_totals: dict[str, float] = {k: 0.0 for k in nutrition_keys}
    nutrition_name_map = {
        "calories": "卡路里",
        "protein": "蛋白质",
        "fat": "脂肪",
        "carbs": "碳水化合物",
    }
    nutrition_unit_map = {
        "calories": "kcal",
        "protein": "g",
        "fat": "g",
        "carbs": "g",
    }

    for meal_name, categories in day_menu.items():
        diners = meal_diners.get(meal_name, 1)
        for cat_name, dishes in categories.items():
            for dish in dishes:
                    dish_id = dish.get("id")
                    full = dish_index.get(dish_id, dish) if dish_id else dish
                    nutrition = full.get("nutrition", {})
                    servings = float(dish.get("quantity") or 1) * diners
                    for key in nutrition_keys:
                        nutrition_totals[key] += float(nutrition.get(key, 0)) * servings

    # 营养素达标计算移到所有meal循环外部，避免重复计算
    for key in nutrition_keys:
        std_val = float(standard_quotas_dict.get(key, 0))
        if std_val > 0:
            actual_per_person = nutrition_totals[key] / daily_diners if daily_diners > 0 else 0
            rate = actual_per_person / std_val
            quota_compliance.append({
                "name": nutrition_name_map[key],
                "actual": round(actual_per_person, 1),
                "standard": round(std_val, 1),
                "rate": round(rate, 2),
                "unit": nutrition_unit_map[key],
            })

    return {
        "passed": True,
        "alerts": [],
        "quota_compliance": quota_compliance,
        "quota_type": quota_type,
    }
