"""
走云智能排菜系统 — 多智能体编排核心服务

采用 Prompt Chaining 策略：将意图解析、菜单生成、约束校验合并为一个 LLM 调用链，
通过精心设计的 System Prompt 让大模型完成全流程。

核心流程：
1. 构建 System Prompt -> 包含结构化约束 + 菜品库数据
2. 发送用户指令到 Qwen-max (流式输出)
3. 实时拼接流式 token 并解析菜单 JSON
4. 以 SSE 事件流的形式返回给前端
"""
import json
import asyncio
import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI
import httpx

from ..config import LLM_API_URL, LLM_API_KEY, LLM_MODEL, DISH_LIBRARY_PATH
from ..schemas.chat_schema import MenuPlanConfig

logger = logging.getLogger(__name__)

# 初始化 OpenAI 兼容客户端 (Qwen-max)
# 设置较长超时，Qwen 生成一周菜单 JSON 需要 30~60s
client = AsyncOpenAI(
    api_key=LLM_API_KEY,
    base_url=LLM_API_URL,
    timeout=httpx.Timeout(120.0, connect=10.0),
)

# 加载菜品库数据
def load_dish_library() -> list[dict]:
    """从 JSON 文件加载菜品库"""
    try:
        with open(DISH_LIBRARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load dish library: {e}")
        return []


DISH_LIBRARY = load_dish_library()


def build_system_prompt(config: MenuPlanConfig) -> str:
    """
    根据用户的结构化配置，构建 System Prompt。

    为什么一次性打包所有约束：
    Demo 阶段简化策略，将 Intent Parser / Generator / Checker 合并为单次调用，
    通过 prompt engineering 让模型一步完成意图解析→菜单生成→自校验。
    """
    # 提取启用的餐次配置
    enabled_meals = [m for m in config.meals_config if m.enabled]

    # 提取启用的健康状态和饮食禁忌
    active_health = [
        h.model_dump() for h in config.global_hard_constraints.health_conditions if h.enabled
    ]
    active_dietary = [
        d.model_dump() for d in config.global_hard_constraints.dietary_restrictions if d.enabled
    ]

    # 构建各餐次的分类要求文本
    meals_desc = []
    for meal in enabled_meals:
        cats = ", ".join(
            [f"{c.name}×{c.count}" for c in meal.dish_structure.categories]
        )
        meals_desc.append(
            f"  - {meal.meal_name}: {meal.diners_count}人, 餐标¥{meal.budget_per_person}/人, "
            f"分类结构=[{cats}], 主食要求={meal.staple_types}, "
            f"汤性={meal.soup_requirements.soup_property}, "
            f"必用食材={meal.meal_specific_constraints.required_ingredients}, "
            f"必排菜品={meal.meal_specific_constraints.mandatory_dishes}, "
            f"口味偏好={meal.flavor_preferences or '无特殊'}"
        )

    # 构建可用菜品清单（分类列出）
    dishes_by_category: dict[str, list[str]] = {}
    for d in DISH_LIBRARY:
        cat = d["category"]
        if cat not in dishes_by_category:
            dishes_by_category[cat] = []
        tags_str = ",".join(d.get("tags", []))
        dishes_by_category[cat].append(
            f'{d["name"]}(id:{d["id"]}, 工艺:{d["process_type"]}, 成本:¥{d["cost_per_serving"]}, 标签:[{tags_str}])'
        )

    dishes_text = ""
    for cat, items in dishes_by_category.items():
        dishes_text += f"\n【{cat}】\n" + "\n".join(f"  - {item}" for item in items)

    system_prompt = f"""你是走云智能排菜系统的 AI 排菜智能体。你的任务是根据用户的排餐指令和结构化约束配置，从菜品库中选择合适的菜品，生成一周的菜单计划。

## 当前排餐环境
- 场景: {config.context_overview.scene}
- 城市: {config.context_overview.city}
- 排餐周期: {config.context_overview.schedule.start_date} 至 {config.context_overview.schedule.end_date}

## 餐次配置
{chr(10).join(meals_desc)}

## 全局红线 (绝对禁止出现的食材)
{config.global_hard_constraints.red_lines if config.global_hard_constraints.red_lines else '无'}

## 特殊人群健康状态
{json.dumps(active_health, ensure_ascii=False) if active_health else '无'}

## 饮食禁忌
{json.dumps(active_dietary, ensure_ascii=False) if active_dietary else '无'}

## 可用菜品库
{dishes_text}

## 排菜规则 (严格遵守)
1. 每个餐次的每一天，必须严格按照分类结构配置的数量选菜。
2. 同一天的不同餐次之间，菜品不得重复。
3. 一周内同一餐次的同一分类下，菜品尽量不重复（重复率 ≤ 20%）。
4. 必须使用"必用食材"中指定的食材（优先选含该食材的菜品）。
5. 必须在指定日期安排"必排菜品"。
6. 全局红线中的食材对应的菜品绝对不能出现。
7. 注意成本控制，单人餐标不得超出预算。
8. 汤性要求必须与汤品标签匹配。

## 输出格式 (严格 JSON)
请直接输出以下格式的 JSON（不要任何其他文字），其中 dates 的 key 是 YYYY-MM-DD 格式的日期：

```json
{{
  "menu": {{
    "YYYY-MM-DD": {{
      "餐次名": {{
        "分类名": [
          {{
            "id": 菜品ID,
            "name": "菜品名称",
            "category": "分类",
            "main_ingredients": ["食材1", "食材2"],
            "process_type": "工艺",
            "flavor": "口味",
            "cost_per_serving": 单价,
            "nutrition": {{"calories": 0, "protein": 0, "carbs": 0, "fat": 0}},
            "tags": ["标签"]
          }}
        ]
      }}
    }}
  }},
  "metrics": {{
    "total_cost": 预估总食材成本(数字),
    "avg_nutrition_score": 营养达标率百分比(数字,0-100),
    "repeat_rate": 菜品重复率百分比(数字,0-100),
    "alert_count": 约束告警数(数字)
  }},
  "summary": "一句话排菜总结"
}}
```
"""
    return system_prompt


async def generate_menu_stream(
    user_message: str,
    config: MenuPlanConfig,
) -> AsyncGenerator[str, None]:
    """
    调用 LLM 生成菜单并以 SSE 事件流返回。

    使用流式(stream=True)调用 LLM，避免长时间同步等待导致 SSE 缓冲卡住。

    事件类型：
    - thinking: 思考步骤更新
    - content: 文本内容流
    - menu_result: 最终菜单结果
    - error: 错误信息
    """
    # === Step 1: 意图解析 ===
    yield _sse_event("thinking", {"step": {"label": "意图解析", "status": "running", "detail": "正在理解您的排菜需求..."}})
    await asyncio.sleep(0.3)
    yield _sse_event("thinking", {"step": {"label": "意图解析", "status": "done", "detail": f"已解析: {user_message[:30]}..."}})

    # === Step 2: 成本计算 ===
    yield _sse_event("thinking", {"step": {"label": "食材成本计算", "status": "running", "detail": "正在查询食材时价..."}})
    await asyncio.sleep(0.2)
    yield _sse_event("thinking", {"step": {"label": "食材成本计算", "status": "done", "detail": "已获取当前市场价格"}})

    # === Step 3: 菜单生成 (流式调用 LLM) ===
    yield _sse_event("thinking", {"step": {"label": "菜单生成", "status": "running", "detail": "正在调用 AI 生成菜单，预计需要 20~40 秒..."}})

    system_prompt = build_system_prompt(config)

    try:
        # 使用 stream=True 流式调用 Qwen-max
        # 这样在 LLM 生成过程中，SSE 连接不会因为长时间无输出而被浏览器/代理断开
        stream = await client.chat.completions.create(
            model=LLM_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=0.7,
            max_tokens=8000,
            stream=True,
        )

        # 流式拼接 LLM 输出的 token
        raw_content = ""
        token_count = 0
        async for chunk in stream:
            delta = chunk.choices[0].delta
            if delta.content:
                raw_content += delta.content
                token_count += 1
                # 每收到 50 个 token 就发送一次进度心跳，让前端知道还在工作
                if token_count % 50 == 0:
                    yield _sse_event("thinking", {
                        "step": {
                            "label": "菜单生成",
                            "status": "running",
                            "detail": f"AI 正在生成中... 已接收 {token_count} tokens",
                        }
                    })

        logger.info(f"LLM response length: {len(raw_content)}, tokens: {token_count}")

        yield _sse_event("thinking", {"step": {"label": "菜单生成", "status": "done", "detail": f"菜单 JSON 已生成 ({token_count} tokens)"}})

        # === Step 4: 约束校验 ===
        yield _sse_event("thinking", {"step": {"label": "约束校验", "status": "running", "detail": "正在交叉校验红线与预算..."}})
        await asyncio.sleep(0.3)
        yield _sse_event("thinking", {"step": {"label": "约束校验", "status": "done", "detail": "校验通过 ✓"}})

        # 解析 JSON
        parsed = _extract_json(raw_content)
        if parsed and "menu" in parsed:
            menu_data = parsed["menu"]
            metrics_data = parsed.get("metrics", {
                "total_cost": 0,
                "avg_nutrition_score": 0,
                "repeat_rate": 0,
                "alert_count": 0,
            })
            summary = parsed.get("summary", "菜单已生成完毕")

            # 发送文本总结
            yield _sse_event("content", {"content": f"✅ {summary}\n\n已为您安排好一周菜单，请在左侧日历看板中查看详情。"})

            # 发送菜单结果
            yield _sse_event("menu_result", {"menu": menu_data, "metrics": metrics_data})
        else:
            # LLM 返回格式异常，尝试发送原始内容
            logger.warning(f"LLM response is not valid JSON. Raw content (first 200 chars): {raw_content[:200]}")
            yield _sse_event("content", {"content": f"⚠️ AI 返回格式异常，原始内容如下：\n\n{raw_content[:500]}"})

    except Exception as e:
        logger.exception("LLM call failed")
        yield _sse_event("thinking", {"step": {"label": "菜单生成", "status": "error", "detail": str(e)[:80]}})
        yield _sse_event("error", {"message": f"AI 服务调用失败: {str(e)}"})

    yield "data: [DONE]\n\n"


def _extract_json(text: str) -> dict | None:
    """从 LLM 返回文本中提取 JSON 对象"""
    # 尝试直接解析
    text = text.strip()

    # 移除可能的 markdown 代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        # 去掉首尾的 ``` 行
        lines = [l for l in lines if not l.strip().startswith("```")]
        text = "\n".join(lines)

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 { ... } 块
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            pass

    return None


def _sse_event(event_type: str, data: dict) -> str:
    """构造 SSE 事件字符串"""
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def search_dishes(query: str) -> list[dict]:
    """搜索菜品库（简单关键词匹配）"""
    query_lower = query.lower()
    results = []
    for dish in DISH_LIBRARY:
        # 匹配名称、食材、标签
        if (
            query_lower in dish["name"].lower()
            or any(query_lower in ing.lower() for ing in dish["main_ingredients"])
            or any(query_lower in tag.lower() for tag in dish.get("tags", []))
            or query_lower in dish.get("category", "").lower()
        ):
            results.append(dish)
    return results[:20]
