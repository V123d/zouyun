"""
走云智能排菜系统 — FastAPI 主入口

职责：
1. 初始化 FastAPI 应用
2. 注册中间件
3. 挂载路由
4. 导入所有智能体（触发自动注册）
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import os

# ==============================================================
# 生产级日志配置
# ==============================================================
os.makedirs("logs", exist_ok=True)
from logging.handlers import RotatingFileHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        RotatingFileHandler("logs/app.log", maxBytes=10*1024*1024, backupCount=5, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# ==============================================================
# 关键步骤：导入所有智能体模块以触发 BaseAgent 的 __init_subclass__ 自动注册。
# 新增智能体时只需在这里加一行 import 即可。
# ==============================================================
from .services import intent_parser      # noqa: F401 — 意图解析智能体
from .services import menu_generator     # noqa: F401 — 菜单生成智能体
from .services import constraint_checker # noqa: F401 — 约束校验智能体
from .services import data_enrichment    # noqa: F401 — 数据补全智能体

# 导入路由
from .routers.chat_router import router as chat_router
from .routers.agent_router import router as agent_router
from .routers.dish_router import router as dish_router
from .routers.menu_router import router as menu_router
from .routers.auth_router import router as auth_router

# 导入智能体注册表
from .services.base_agent import AgentRegistry
from .schemas.chat_schema import NotImplementedResponse

app = FastAPI(
    title="走云智能排菜系统 API",
    version="2.0.0",
    description=(
        "中学食堂智能排菜系统后端服务 — 多智能体架构\n\n"
        "本系统由多个独立智能体协同工作：\n"
        "- **意图解析**: 自然语言 → 结构化需求\n"
        "- **菜单生成**: 从菜品库选菜组装菜单\n"
        "- **约束校验**: 确定性规则引擎校验\n"
        "- **数据补全**: 补全菜品完整属性\n\n"
        "智能体注册表: `GET /api/agents`\n"
        "编排排菜: `POST /api/chat/send` (SSE)\n"
        "独立调用: `POST /api/agents/{agent-id}`"
    ),
)

import os
from fastapi.responses import JSONResponse
from fastapi.requests import Request

# CORS 配置
allowed_origins_str = os.environ.get("ALLOWED_ORIGINS", "*")
allowed_origins = [origin.strip() for origin in allowed_origins_str.split(",")] if allowed_origins_str != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常拦截器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(f"Global exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False, 
            "message": "服务器内部错误，请稍后再试", 
            "detail": str(exc) if os.environ.get("DEBUG") == "True" else None
        }
    )

# 挂载路由
app.include_router(chat_router)
app.include_router(agent_router)
app.include_router(dish_router)
app.include_router(menu_router)
app.include_router(auth_router, prefix="/api/auth", tags=["auth"])


# ============================================================
# 占位 API — 待开发功能
# ============================================================

@app.post("/api/pricing/sync")
async def pricing_sync():
    """生鲜时价同步（待开发）"""
    return NotImplementedResponse(message="生鲜时价同步接口正在对接中")

@app.post("/api/inventory/sync")
async def inventory_sync():
    """库存数据同步（待开发）"""
    return NotImplementedResponse(message="库存数据同步接口正在对接中")


# ============================================================
# 健康检查
# ============================================================

@app.get("/api/health")
async def health_check():
    """健康检查 — 展示系统状态和已注册智能体数量"""
    from .database import AsyncSessionLocal
    from .models.dish import Dish
    from sqlalchemy import select, func
    
    async with AsyncSessionLocal() as session:
        res = await session.execute(select(func.count(Dish.id)))
        dish_count = res.scalar() or 0
        
    agents = AgentRegistry.list_all()
    return {
        "status": "ok",
        "dish_count": dish_count,
        "agent_count": len(agents),
        "agents": [a["id"] for a in agents],
    }


if __name__ == "__main__":
    import uvicorn
    from .config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
