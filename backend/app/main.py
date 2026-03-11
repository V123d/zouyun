"""
走云智能排菜系统 — FastAPI 主入口

提供核心 API：
- POST /api/chat/send (SSE) — 智能排菜对话
- GET  /api/dishes/search   — 菜品搜索
- GET  /api/dishes/library  — 菜品库列表
- 占位 API（待开发功能）
"""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from .schemas.chat_schema import ChatRequest, NotImplementedResponse
from .services.agent_service import generate_menu_stream, search_dishes, DISH_LIBRARY

# 日志配置
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

app = FastAPI(
    title="走云智能排菜系统 API",
    version="1.0.0",
    description="中学食堂智能排菜系统后端服务",
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# 核心 API
# ============================================================

@app.post("/api/chat/send")
async def chat_send(request: ChatRequest):
    """
    智能排菜对话接口 (SSE)

    接收用户消息和完整的规则配置 JSON，触发多 Agent 流程，
    以 Server-Sent Events 格式流式返回思考进度和菜单结果。
    """
    return StreamingResponse(
        generate_menu_stream(request.message, request.config),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@app.get("/api/dishes/search")
async def dishes_search(q: str = ""):
    """搜索菜品库"""
    if not q.strip():
        return []
    return search_dishes(q.strip())


@app.get("/api/dishes/library")
async def dishes_library():
    """获取完整菜品库"""
    return DISH_LIBRARY


# ============================================================
# 占位 API — 待开发功能
# ============================================================

@app.get("/api/report/nutrition")
async def report_nutrition():
    """营养报告生成（待开发）"""
    return NotImplementedResponse(message="营养报告生成功能正在开发中，敬请期待")


@app.get("/api/report/recipe/{dish_id}")
async def report_recipe(dish_id: int):
    """定量配方查看（待开发）"""
    return NotImplementedResponse(message=f"菜品(ID:{dish_id})的定量配方功能正在开发中")


@app.post("/api/pricing/sync")
async def pricing_sync():
    """生鲜时价同步（待开发）"""
    return NotImplementedResponse(message="生鲜时价同步接口正在对接中")


@app.post("/api/inventory/sync")
async def inventory_sync():
    """库存数据同步（待开发）"""
    return NotImplementedResponse(message="库存数据同步接口正在对接中")


@app.post("/api/plan/save")
async def plan_save():
    """保存排餐计划（待开发）"""
    return NotImplementedResponse(message="排餐计划保存功能正在开发中")


@app.get("/api/plan/{plan_id}")
async def plan_detail(plan_id: int):
    """获取排餐计划详情（待开发）"""
    return NotImplementedResponse(message=f"排餐计划(ID:{plan_id})详情功能正在开发中")


# ============================================================
# 健康检查
# ============================================================

@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "dish_count": len(DISH_LIBRARY)}


if __name__ == "__main__":
    import uvicorn
    from .config import HOST, PORT
    uvicorn.run(app, host=HOST, port=PORT)
