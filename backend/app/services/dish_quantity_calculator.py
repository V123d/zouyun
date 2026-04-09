"""
走云智能排菜系统 — 排菜份数计算服务

根据「食堂菜品结构」和「个人菜品结构」计算每道菜的排菜份数。

计算公式：
    某分类每道份数 = ceil(就餐人数 × 个人该分类份数 / 食堂该分类菜品数量)

例如：
- 500 人，每人 2 道荤菜 → 共 1000 份荤菜
- 食堂排 5 道荤菜 → 每道荤菜 ceil(1000/5) = 200 份
"""
import math
import logging
from typing import Any

from ..schemas.chat_schema import MenuPlanConfig, MealConfig, DishCategory

logger = logging.getLogger(__name__)


def _match_category_name(cat_name: str, personal_cat_name: str) -> bool:
    """
    判断食堂菜品分类和个人配置分类是否匹配。

    匹配规则（按优先级）：
    1. 完全相同
    2. 个人配置分类名包含在食堂分类名中
    3. 食堂分类名包含在个人配置分类名中
    4. 常见同义词映射：荤菜 ↔ 猪肉类/鸡鸭禽类/鱼虾海鲜类/牛羊肉类
       素菜 ↔ 蔬菜类/豆制品类/菌菇类
    """
    cat_lower = cat_name.lower()
    personal_lower = personal_cat_name.lower()

    # 1. 完全相同
    if cat_name == personal_cat_name:
        return True

    # 2. 包含关系
    if personal_lower in cat_lower or cat_lower in personal_lower:
        return True

    # 3. 同义词映射
    meat_aliases = {'荤菜', '大荤', '肉菜', '肉类'}
    vegetable_aliases = {'素菜', '素', '青菜', '蔬菜'}
    staple_aliases = {'主食', '面点', '米饭', '面食'}
    soup_aliases = {'汤', '汤品', '羹', '例汤'}

    # 荤菜匹配
    meat_categories = {'猪肉类', '鸡鸭禽类', '鱼虾海鲜类', '牛羊肉类', '畜肉类', '禽肉类', '海鲜类'}
    if personal_cat_name in meat_aliases and cat_name in meat_categories:
        return True

    # 素菜匹配
    veg_categories = {'蔬菜类', '豆制品类', '菌菇类', '凉菜'}
    if personal_cat_name in vegetable_aliases and cat_name in veg_categories:
        return True

    # 主食匹配
    if personal_cat_name in staple_aliases and cat_name in {'主食', '面点类', '面食类'}:
        return True

    # 汤匹配
    if personal_cat_name in soup_aliases and cat_name in {'汤羹类', '汤类', '汤'}:
        return True

    return False


def calculate_dish_quantities(
    config: MenuPlanConfig,
    day_menu: dict[str, Any]
) -> dict[str, Any]:
    """
    计算每道菜的份数，注入到菜品数据中。

    参数:
        config: 排餐配置（包含所有餐次的配置）
        day_menu: 某天菜单，格式为 {meal_name: {category_name: [dish, ...], ...}, ...}

    返回:
        同输入结构，但每道菜品增加 `quantity` 字段（向上取整的份数）
    """
    # 构建 meal_name -> MealConfig 的映射
    meal_config_map: dict[str, MealConfig] = {}
    for mc in config.meals_config:
        if mc.enabled:
            meal_config_map[mc.meal_name] = mc

    result_menu = {}

    for meal_name, categories_data in day_menu.items():
        # 查找该餐次的配置
        meal_config = meal_config_map.get(meal_name)
        if not meal_config:
            logger.warning(f"找不到餐次配置: {meal_name}，份数设为默认值1")
            result_menu[meal_name] = {
                cat_name: [
                    {**dish, 'quantity': 1} for dish in dishes
                ] for cat_name, dishes in categories_data.items()
            }
            continue

        diners_count = meal_config.diners_count
        personal_structure = meal_config.meal_specific_constraints.personal_dish_structure

        # 构建个人配置映射
        personal_map: dict[str, int] = {}
        if personal_structure and personal_structure.categories:
            for pc in personal_structure.categories:
                personal_map[pc.name] = pc.count

        updated_categories = {}

        for cat_name, dishes in categories_data.items():
            if not dishes:
                updated_categories[cat_name] = []
                continue

            # 查找匹配的个人配置分类
            matched_personal_count = 0
            for personal_name, personal_count in personal_map.items():
                if _match_category_name(cat_name, personal_name):
                    matched_personal_count = personal_count
                    break

            if matched_personal_count == 0:
                # 无法匹配，使用默认份数 1
                logger.debug(f"分类 '{cat_name}' 无法匹配个人配置，使用默认份数1")
                updated_categories[cat_name] = [
                    {**dish, 'quantity': 1} for dish in dishes
                ]
                continue

            # 计算该分类每道菜的份数
            total_needed = diners_count * matched_personal_count
            dish_count = len(dishes)
            quantity_per_dish = math.ceil(total_needed / dish_count)

            logger.info(
                f"份数计算: {meal_name}/{cat_name}, "
                f"就餐人数={diners_count}, 每人份数={matched_personal_count}, "
                f"总需求={total_needed}, 菜品数={dish_count}, "
                f"每道份数={quantity_per_dish}"
            )

            # 为每道菜注入份数字段
            updated_dishes = []
            for dish in dishes:
                dish_copy = dict(dish)
                dish_copy['quantity'] = quantity_per_dish
                updated_dishes.append(dish_copy)

            updated_categories[cat_name] = updated_dishes

        result_menu[meal_name] = updated_categories

    return result_menu