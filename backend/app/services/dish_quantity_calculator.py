"""
走云智能排菜系统 — 排菜份数计算服务

根据「食堂菜品结构」和「个人菜品结构」计算每道菜的排菜份数。

核心逻辑：
1. 自动识别菜品结构中的标签，补充个人配置
2. 按标签聚合后统一计算份数

计算公式：
    某标签每道份数 = ceil(就餐人数 × 个人该标签份数 / 该标签下菜品总数)
"""
import math
import logging
from typing import Any

from ..schemas.chat_schema import MenuPlanConfig, MealConfig, DishCategory

logger = logging.getLogger(__name__)


# 定义标准标签列表
STANDARD_TAGS = ['主食', '荤菜', '素菜', '凉菜', '汤类']


def _get_tag_for_category(dishes: list[dict]) -> str | None:
    """
    根据菜品tags判断该分类属于哪个标准标签
    
    返回第一个匹配的标准标签，如无匹配返回None
    """
    for dish in dishes:
        tags = dish.get("tags", [])
        if isinstance(tags, list):
            for tag in STANDARD_TAGS:
                if tag in tags:
                    return tag
    return None


def _auto_fill_personal_structure(
    categories_data: dict[str, list[dict]],
    personal_map: dict[str, int]
) -> dict[str, int]:
    """
    自动识别菜品结构中的标签，补充到个人配置中
    
    如果某分类属于某标签（如排骨菜系→荤菜），但个人配置中没有该标签，自动添加
    返回完整的个人配置映射（标签 → 份数）
    """
    result = dict(personal_map)  # 复制现有配置
    
    for cat_name, dishes in categories_data.items():
        if not dishes:
            continue
        
        tag = _get_tag_for_category(dishes)
        if tag and tag not in result:
            # 自动补充该标签，默认份数为1
            result[tag] = 1
            logger.info(f"自动补充标签 '{tag}'（来自分类 '{cat_name}'）到个人配置")
    
    return result


def _calculate_quantities_by_tag(
    categories_data: dict[str, list[dict]],
    personal_map: dict[str, int],
    diners_count: int
) -> dict[str, int]:
    """
    按标签聚合后计算份数
    
    返回: { "cat_name": 每道份数, ... }
    """
    # 第一步：按标签分组统计菜品
    tag_to_categories: dict[str, list[str]] = {}
    tag_to_dish_count: dict[str, int] = {}
    
    for cat_name, dishes in categories_data.items():
        if not dishes:
            continue
        
        tag = _get_tag_for_category(dishes)
        if tag:
            if tag not in tag_to_categories:
                tag_to_categories[tag] = []
                tag_to_dish_count[tag] = 0
            tag_to_categories[tag].append(cat_name)
            tag_to_dish_count[tag] += len(dishes)
            logger.debug(f"分类 '{cat_name}' 属于标签 '{tag}'，包含 {len(dishes)} 道菜品")
    
    # 第二步：按标签计算份数
    tag_to_quantity: dict[str, int] = {}
    for tag, dish_count in tag_to_dish_count.items():
        personal_count = personal_map.get(tag, 1)  # 默认1份
        total_needed = diners_count * personal_count
        quantity_per_dish = math.ceil(total_needed / dish_count)
        tag_to_quantity[tag] = quantity_per_dish
        logger.info(
            f"标签'{tag}'份数计算: 就餐{diners_count}人 × {personal_count}份/人 = {total_needed}份, "
            f"共{dish_count}道菜, 每道{quantity_per_dish}份"
        )
    
    # 第三步：生成每个分类的份数
    result = {}
    for tag, cat_names in tag_to_categories.items():
        qty = tag_to_quantity[tag]
        for cat_name in cat_names:
            result[cat_name] = qty
    
    return result


def calculate_dish_quantities(
    config: MenuPlanConfig,
    day_menu: dict[str, Any],
) -> dict[str, Any]:
    """
    计算每道菜的份数，注入到菜品数据中。

    参数:
        config: 排餐配置（包含所有餐次的配置）
        day_menu: 某天菜单，格式为 {meal_name: {category_name: [dish, ...], ...}, ...}
                  菜品数据中应包含 tags 字段

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

        logger.info(f"餐次 {meal_name} 原始个人配置: {personal_map}")

        # 自动补充个人配置中缺失的标签
        personal_map = _auto_fill_personal_structure(categories_data, personal_map)

        logger.info(f"餐次 {meal_name} 补充后个人配置: {personal_map}")

        # 按标签聚合计算份数
        cat_quantities = _calculate_quantities_by_tag(
            categories_data, personal_map, diners_count
        )

        updated_categories = {}

        for cat_name, dishes in categories_data.items():
            if not dishes:
                updated_categories[cat_name] = []
                continue

            quantity_per_dish = cat_quantities.get(cat_name, 1)
            logger.info(f"份数分配: {meal_name}/{cat_name}, 每道{quantity_per_dish}份")

            # 为每道菜注入份数字段
            updated_dishes = []
            for dish in dishes:
                dish_copy = dict(dish)
                dish_copy['quantity'] = quantity_per_dish
                updated_dishes.append(dish_copy)

            updated_categories[cat_name] = updated_dishes

        result_menu[meal_name] = updated_categories

    return result_menu
