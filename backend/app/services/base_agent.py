"""
走云智能排菜系统 — 智能体基类与自动注册机制

所有智能体继承 BaseAgent，通过 __init_subclass__ 实现自动注册。
新增智能体只需：
  1. 创建新文件，继承 BaseAgent
  2. 填写 agent_id / agent_name / agent_description / agent_type
  3. 实现 execute() 方法
即可自动出现在注册表和 API 路由中，无需手动修改其他文件。
"""
import time
import logging
from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, ClassVar

logger = logging.getLogger(__name__)


class AgentRegistry:
    """智能体注册表（全局单例）"""

    _agents: dict[str, "BaseAgent"] = {}

    @classmethod
    def register(cls, agent: "BaseAgent") -> None:
        """注册一个智能体实例"""
        cls._agents[agent.agent_id] = agent
        logger.debug(f"Agent registered: {agent.agent_id} ({agent.agent_type})")

    @classmethod
    def get(cls, agent_id: str) -> "BaseAgent | None":
        """按 ID 获取智能体"""
        return cls._agents.get(agent_id)

    @classmethod
    def list_all(cls) -> list[dict[str, Any]]:
        """返回所有已注册智能体的描述信息（供 /api/agents 接口使用）"""
        return [
            {
                "id": agent.agent_id,
                "name": agent.agent_name,
                "description": agent.agent_description,
                "type": agent.agent_type,
                "status": "active",
                "endpoint": f"/api/agents/{agent.agent_id}",
            }
            for agent in cls._agents.values()
        ]


class BaseAgent(ABC):
    """
    智能体基类。

    子类必须定义以下类变量：
    - agent_id:          唯一标识（kebab-case），同时作为 API 路由名
    - agent_name:        展示名称（中英文皆可）
    - agent_description: 功能描述
    - agent_type:        类型标签（'llm' | 'rule'）

    子类必须实现：
    - execute(**kwargs) -> dict  执行智能体核心逻辑

    子类可选实现：
    - execute_stream(**kwargs) -> AsyncGenerator  流式执行（LLM 型智能体）
    """

    agent_id: ClassVar[str]
    agent_name: ClassVar[str]
    agent_description: ClassVar[str]
    agent_type: ClassVar[str]  # 'llm' | 'rule'

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """自动注册：任何继承 BaseAgent 的子类在导入时即完成注册"""
        super().__init_subclass__(**kwargs)
        # 跳过没有定义 agent_id 的中间抽象类
        if hasattr(cls, "agent_id") and cls.agent_id:
            AgentRegistry.register(cls())

    async def run(self, **kwargs: Any) -> dict[str, Any]:
        """
        执行入口（含统一计时日志 + 异常保护）。

        为什么包装 execute()：
        所有智能体共享一套日志和错误处理逻辑，避免在每个子类中重复实现。
        外部调用方应优先使用 run()，不直接调用 execute()。

        Args:
            **kwargs: 各智能体自定义的输入参数

        Returns:
            结构化的输出字典，异常时包含 success=False 和 error 字段
        """
        t0 = time.monotonic()
        try:
            result = await self.execute(**kwargs)
            elapsed = time.monotonic() - t0
            logger.info(f"[{self.agent_id}] execute done in {elapsed:.2f}s")
            return result
        except Exception as e:
            elapsed = time.monotonic() - t0
            logger.exception(f"[{self.agent_id}] execute failed after {elapsed:.2f}s")
            return {"success": False, "error": str(e)}

    @abstractmethod
    async def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        执行智能体核心逻辑（子类实现）。

        Args:
            **kwargs: 各智能体自定义的输入参数

        Returns:
            结构化的输出字典
        """
        ...

    async def execute_stream(self, **kwargs: Any) -> AsyncGenerator[Any, None]:
        """
        流式执行（可选，LLM 型智能体按需覆盖）。

        默认实现抛出 NotImplementedError，要求流式执行的子类必须覆盖此方法。

        Yields:
            子类自定义的流式数据块
        """
        raise NotImplementedError(f"{self.agent_id} does not support streaming")
        # 使生成器语法有效（yield 语句必须存在于生成器函数体内）
        yield  # pragma: no cover
