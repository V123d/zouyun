"""
走云智能排菜系统 — 共享工具模块

提取各智能体中重复使用的工具函数和数据，避免代码重复。
"""
import json
import logging
from pathlib import Path
from typing import Any

from ..config import DISH_LIBRARY_PATH

logger = logging.getLogger(__name__)


# ── 菜品库数据（全局加载一次） ──────────────────────────────────

def _load_dish_library() -> list[dict[str, Any]]:
    """从 JSON 文件加载菜品库"""
    try:
        with open(DISH_LIBRARY_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load dish library: {e}")
        return []


DISH_LIBRARY: list[dict[str, Any]] = _load_dish_library()

DISH_INDEX: dict[int, dict[str, Any]] = {d["id"]: d for d in DISH_LIBRARY}
"""菜品 ID → 完整数据的索引，用于快速查找和补全。"""


# ── JSON 提取 ────────────────────────────────────────────────

def extract_json(text: str) -> dict[str, Any] | None:
    """
    从 LLM 返回文本中提取 JSON 对象。

    为什么需要多轮尝试：
    LLM 返回的文本可能包含 markdown 代码块包裹、前后多余文字等噪声，
    需要逐步尝试直接解析 → 去除 markdown 标记 → 截取 { ... } 子串。

    Args:
        text: LLM 返回的原始文本

    Returns:
        解析成功返回 dict，失败返回 None
    """
    text = text.strip()

    # 移除 markdown 代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)

    # 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 尝试提取 { ... } 块
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start: end + 1])
        except json.JSONDecodeError:
            pass

    return None


# ── SSE 事件构造 ──────────────────────────────────────────────

def sse(event_type: str, data: dict[str, Any]) -> str:
    """
    构造 SSE 事件字符串。

    Args:
        event_type: 事件类型（thinking / content / menu_update / menu_remove / menu_result / error / constraint_alert）
        data: 事件数据

    Returns:
        格式化的 SSE data 行
    """
    payload = {"type": event_type, **data}
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def fix_partial_json(s: str) -> str:
    """修复截断的 JSON 字符串（主要用于流式解析大模型输出）。"""
    s = s.strip()
    if not s: return "{}"
    
    in_string = False
    escape = False
    for i, c in enumerate(s):
        if c == '"' and not escape:
            in_string = not in_string
        if c == '\\' and not escape:
            escape = True
        else:
            escape = False
            
    if in_string:
        s = s[:s.rfind('"')]
    
    stack = []
    escape = False
    in_string = False
    for c in s:
        if c == '"' and not escape:
            in_string = not in_string
        elif not in_string:
            if c in '{[':
                stack.append(c)
            elif c == '}':
                if stack and stack[-1] == '{': stack.pop()
            elif c == ']':
                if stack and stack[-1] == '[': stack.pop()
        
        if c == '\\' and not escape:
            escape = True
        else:
            escape = False

    for c in reversed(stack):
        if c == '{': s += '}'
        elif c == '[': s += ']'
        
    return s


def extract_partial_json(text: str) -> dict[str, Any] | None:
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        lines = [line for line in lines if not line.strip().startswith("```")]
        text = "\n".join(lines)
        
    start = text.find("{")
    if start == -1: return None
    
    fixed = fix_partial_json(text[start:])
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        return None

