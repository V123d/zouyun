"""
走云智能排菜系统 — 约束校验智能体

职责：对生成的菜单进行确定性规则校验（纯 Python，不依赖 LLM）。
校验项：红线食材扫描、预算超标检测、菜品重复率、分类数量匹配、跨餐重复。

修复记录：
- v2: 修复预算校验（之前 meal_budgets 构建了但从未使用）
- v2: 成本计算现已考虑就餐人数（diners_count）
- v2: 营养评分基于菜品库实际数据计算，不再硬编码 85
"""
import logging
from collections import Counter
from typing import Any

from .base_agent import BaseAgent
from .utils import DISH_INDEX
from ..schemas.chat_schema import ConstraintAlert

logger = logging.getLogger(__name__)


class ConstraintCheckerAgent(BaseAgent):
    """约束校验智能体（纯规则引擎，不调用 LLM）"""

    agent_id = "constraint-checker"
    agent_name = "Constraint Checker / 约束校验智能体"
    agent_description = "对生成的菜单进行确定性规则校验：红线食材扫描、预算超标检测、菜品重复率计算、分类数量匹配验证"
    agent_type = "rule"

    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        执行完整菜单约束校验。

        Args:
            menu:   菜单 JSON（{date: {meal_name: {category: [dishes]}}}）
            config: MenuPlanConfig 对象或其 dict 形式

        Returns:
            {
                passed:  bool,            所有校验均通过
                alerts:  list[str],       具体不合格项描述（每条可读）
                metrics: {
                    total_cost:          float, 总食材成本（已乘就餐人数）
                    avg_nutrition_score: float, 营养达标率 0-100
                    repeat_rate:         float, 菜品重复率 %
                    alert_count:         int,
                    total_dishes:        int,
                    unique_dishes:       int,
                }
            }
        """
        menu: dict = kwargs.get("menu", {})
        config: Any = kwargs.get("config", {})

        return _check_menu(menu, config)


def _check_menu(menu: dict, config: Any, daily_configs: dict = None) -> dict[str, Any]:
    """
    内部校验逻辑，支持完整菜单校验。

    拆为独立函数方便编排器直接调用，无需通过智能体实例。
    """
    alerts: list[dict] = []
    total_cost_raw = 0.0      # 未乘人数的原始成本（所有道菜 cost_per_serving 之和）
    total_dishes = 0
    dish_name_counter: dict[str, int] = {}
    nutrition_scores: list[float] = []  # 每道菜的营养评分（calories 合理性，0-100）

    # ── 提取约束配置 ─────────────────────────────────────────────
    if isinstance(config, dict):
        ghc = config.get("global_hard_constraints", {})
        red_lines: set[str] = set(ghc.get("red_lines", []))
        meals_config_list: list[dict] = config.get("meals_config", [])
    else:
        red_lines = set(config.global_hard_constraints.red_lines)
        meals_config_list = [m.model_dump() for m in config.meals_config]

    # ── 构建餐次配置索引 ─────────────────────────────────────────
    meal_budgets: dict[str, float] = {}         # meal_name -> budget_per_person
    meal_diners: dict[str, int] = {}            # meal_name -> diners_count
    meal_structures: dict[str, dict[str, int]] = {}  # meal_name -> {category: count}
    meal_process_limits: dict[str, dict[str, int]] = {}  # meal_name -> {process_type: max}

    for mc in meals_config_list:
        if mc.get("enabled", True):
            meal_name = mc["meal_name"]
            meal_budgets[meal_name] = mc.get("budget_per_person", 999.0)
            meal_diners[meal_name] = mc.get("diners_count", 1)
            meal_structures[meal_name] = {
                cat["name"]: cat["count"]
                for cat in mc.get("dish_structure", {}).get("categories", [])
            }
            meal_process_limits[meal_name] = {
                pl["process_type"]: pl["max_count"]
                for pl in mc.get("process_limits", [])
                if pl.get("process_type") and pl.get("max_count")
            }

    # 用于跨天重复检测的全局字典：(dish_name, cat_name) -> [出现日期列表]
    # 主食和汤类天然重复率高，允许跨天甚至同日重复
    ALLOW_REPEAT_CATEGORIES: set[str] = {"主食", "汤"}
    # 素菜允许隔天重复
    EVERY_OTHER_DAY_CATEGORIES: set[str] = {"素菜"}
    cross_day_tracker: dict[tuple[str, str], list[str]] = {}

    # ── 逐日逐餐校验 ─────────────────────────────────────────────
    for date, meals in menu.items():
        daily_dish_names: set[str] = set()  # 同日跨餐去重

        if daily_configs and date in daily_configs:
            d_conf = daily_configs[date]
            d_list = d_conf.get("meals_config", []) if isinstance(d_conf, dict) else [m.model_dump() for m in d_conf.meals_config]
            d_meal_structures = {mc["meal_name"]: {c["name"]: c["count"] for c in mc.get("dish_structure", {}).get("categories", [])} for mc in d_list if mc.get("enabled", True)}
            d_meal_budgets = {mc["meal_name"]: mc.get("budget_per_person", 999.0) for mc in d_list if mc.get("enabled", True)}
            d_meal_process_limits = {mc["meal_name"]: {pl["process_type"]: pl["max_count"] for pl in mc.get("process_limits", []) if pl.get("process_type") and pl.get("max_count")} for mc in d_list if mc.get("enabled", True)}
            d_meal_diners = {mc["meal_name"]: mc.get("diners_count", 1) for mc in d_list if mc.get("enabled", True)}
        else:
            d_meal_structures = meal_structures
            d_meal_budgets = meal_budgets
            d_meal_process_limits = meal_process_limits
            d_meal_diners = meal_diners

        for meal_name, categories in meals.items():
            meal_cost_per_person = 0.0  # 本餐次单人成本
            diners = d_meal_diners.get(meal_name, 1)
            budget = d_meal_budgets.get(meal_name, 999.0)

            for cat_name, dishes in categories.items():
                # ── 分类数量校验 ──
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

                    # 从菜品库取完整数据（LLM 紧凑格式只有 id/name）
                    full = DISH_INDEX.get(dish_id, dish) if dish_id else dish
                    ingredients: list[str] = full.get("main_ingredients", [])
                    cost: float = float(full.get("cost_per_serving", 0))

                    # ── 红线食材扫描 ──
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

                    # ── 成本累计（单人份） ──
                    meal_cost_per_person += cost
                    total_cost_raw += cost

                    # ── 重复率统计 ──
                    if cat_name not in ALLOW_REPEAT_CATEGORIES:
                        dish_name_counter[dish_name] = dish_name_counter.get(dish_name, 0) + 1

                    # ── 同日跨餐重复检查 ──
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

                    # ── 跨天重复追踪（主食/汤类豁免） ──
                    if cat_name not in ALLOW_REPEAT_CATEGORIES:
                        cross_day_tracker.setdefault((dish_name, cat_name), []).append(date)

                    # ── 营养评分（以 calories 是否在合理区间为简单指标） ──
                    nutrition = full.get("nutrition", {})
                    calories = float(nutrition.get("calories", 0))
                    if calories > 0:
                        # 单道菜热量合理区间：50~600 kcal
                        score = min(100.0, max(0.0, 100.0 - abs(calories - 300) / 3.0))
                        nutrition_scores.append(score)

            # ── 工艺集中度告警（同餐次同工艺菜品超限） ──
            limits = d_meal_process_limits.get(meal_name, {})
            if limits:
                process_counter: Counter[str] = Counter()
                for cat_dishes in categories.values():
                    for dish in cat_dishes:
                        full_d = DISH_INDEX.get(dish.get("id"), dish) if dish.get("id") else dish
                        proc = full_d.get("process_type", "")
                        if proc:
                            process_counter[proc] += 1
                for proc, count in process_counter.items():
                    max_count = limits.get(proc)
                    if max_count is not None and count > max_count:
                        alerts.append(ConstraintAlert(
                            type="PROCESS_CONCENTRATION",
                            date=date,
                            meal_name=meal_name,
                            detail=f"工艺「{proc}」出现 {count} 道，限制 {max_count} 道"
                        ).model_dump())

            # ── 预算校验（单人成本 vs 餐标） ──
            if meal_cost_per_person > budget * 1.05:  # 允许 5% 宽容
                alerts.append(ConstraintAlert(
                    type="BUDGET_OVERFLOW",
                    date=date,
                    meal_name=meal_name,
                    detail=f"单人成本 ¥{meal_cost_per_person:.1f}，餐标 ¥{budget:.1f}，超出 {(meal_cost_per_person/budget - 1)*100:.0f}%"
                ).model_dump())

    # ── 跨天重复告警 ─────────────────────────────────────────────
    from datetime import date as date_cls
    for (dish_name, cat_name), dates in cross_day_tracker.items():
        if len(dates) > 1:
            sorted_dates = sorted(list(set(dates)))
            if cat_name in EVERY_OTHER_DAY_CATEGORIES:
                # 允许隔天重复，相邻出现差必须 >= 2
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
                # 荤菜等其他类别允许间隔3天重复，相邻出现差必须 >= 4
                for i in range(1, len(sorted_dates)):
                    d1 = date_cls.fromisoformat(sorted_dates[i-1])
                    d2 = date_cls.fromisoformat(sorted_dates[i])
                    if (d2 - d1).days <= 3:
                        alerts.append(ConstraintAlert(
                            type="CROSS_DAY_DUPLICATE",
                            date=sorted_dates[i],
                            meal_name="",
                            dish_name=dish_name,
                            detail=f"「{cat_name}」在 {sorted_dates[i-1]} 和 {sorted_dates[i]} 间隔过近重复出现"
                        ).model_dump())
                        break

    # ── 汇总指标 ─────────────────────────────────────────────────
    total_non_exempt = sum(dish_name_counter.values())
    unique_count = len(dish_name_counter)
    repeat_rate = round((total_non_exempt - unique_count) / total_non_exempt * 100, 1) if total_non_exempt > 0 else 0.0

    # ── 重复率阈值告警（超 30% 触发，驱动重试） ──
    MAX_REPEAT_RATE = 30.0
    if repeat_rate > MAX_REPEAT_RATE:
        alerts.append(ConstraintAlert(
            type="HIGH_REPEAT_RATE",
            date="全局",
            meal_name="",
            detail=f"菜品重复率 {repeat_rate}% 超过阈值 {MAX_REPEAT_RATE}%"
        ).model_dump())

    total_cost = _calc_total_cost(menu, meal_diners, daily_configs)
    avg_nutrition = round(sum(nutrition_scores) / len(nutrition_scores), 1) if nutrition_scores else 0.0

    return {
        "success": True,
        "passed": len(alerts) == 0,
        "alerts": alerts,
        "metrics": {
            "total_cost": round(total_cost, 2),
            "avg_nutrition_score": avg_nutrition,
            "repeat_rate": repeat_rate,
            "alert_count": len(alerts),
            "total_dishes": total_dishes,
            "unique_dishes": unique_count,
        },
    }


def _calc_total_cost(menu: dict, meal_diners: dict[str, int], daily_configs: dict = None) -> float:
    """
    按餐次 × 就餐人数计算总食材成本。

    为什么单独提取：
    total_cost 需要每道菜的 cost_per_serving × 该餐次的 diners_count，
    不同餐次人数不同，不能统一乘以一个系数。
    """
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
                    full = DISH_INDEX.get(dish_id, dish) if dish_id else dish
                    cost = float(full.get("cost_per_serving", 0))
                    total += cost * diners
    return total
