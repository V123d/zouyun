import os
import json
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from ..services.constraint_checker import _check_menu

router = APIRouter(prefix="/api/menu", tags=["菜单管理"])

HISTORY_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "history")
os.makedirs(HISTORY_DIR, exist_ok=True)

logger = logging.getLogger(__name__)

class RecalculateRequest(BaseModel):
    menu: Dict[str, Any]
    config: Dict[str, Any]

@router.post("/recalculate")
async def recalculate_menu(req: RecalculateRequest):
    """
    接收手动修改后的菜单及配置，调用规则引擎重新计算成本、营养、重复率及约束告警
    """
    try:
        result = _check_menu(req.menu, req.config)
        # 将原始 metrics 与可读的告警合并返回
        final_alerts_readable = [
            f"[{a.get('type', '')}] {a.get('date', '')} "
            f"{a.get('meal_name', '')}"
            f"{'/' + a.get('category', '') if a.get('category') else ''}"
            f"{'/' + a.get('dish_name', '') if a.get('dish_name') else ''}"
            f": {a.get('detail', '')}"
            for a in result.get("alerts", [])
        ]
        return {
            "success": True, 
            "metrics": {
                **result.get("metrics", {}),
                "alerts": final_alerts_readable
            }
        }
    except Exception as e:
        logger.exception("Recalculate error")
        raise HTTPException(status_code=500, detail=str(e))


class SaveHistoryRequest(BaseModel):
    menu: Dict[str, Any]
    metrics: Dict[str, Any]
    config: Dict[str, Any]
    name: Optional[str] = None

@router.post("/history")
async def save_history(req: SaveHistoryRequest):
    """
    保存当前完整排餐结果至历史记录
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_id = f"plan_{timestamp}"
    filename = os.path.join(HISTORY_DIR, f"{record_id}.json")
    
    data = {
        "id": record_id,
        "name": req.name or f"排餐方案 {datetime.now().strftime('%m-%d %H:%M')}",
        "timestamp": datetime.now().isoformat(),
        "menu": req.menu,
        "metrics": req.metrics,
        "config": req.config
    }
    
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return {"success": True, "id": record_id, "message": "保存成功"}
    except Exception as e:
        logger.exception("Save history error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def list_history():
    """
    列出所有历史排餐记录（不含全量子菜单，仅返回元信息）
    """
    records = []
    try:
        if not os.path.exists(HISTORY_DIR):
            return {"success": True, "records": []}
            
        for fname in os.listdir(HISTORY_DIR):
            if fname.endswith(".json"):
                path = os.path.join(HISTORY_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        records.append({
                            "id": data.get("id"),
                            "name": data.get("name"),
                            "timestamp": data.get("timestamp"),
                            "metrics": data.get("metrics")
                        })
                except Exception as file_e:
                    logger.warning(f"Failed to read history file {fname}: {file_e}")
                    
        # Sort by timestamp desc
        records.sort(key=lambda x: x["timestamp"] if x.get("timestamp") else "", reverse=True)
        return {"success": True, "records": records}
    except Exception as e:
        logger.exception("List history error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{record_id}")
async def get_history(record_id: str):
    """
    获取单条历史记录的完整详情内容
    """
    filename = os.path.join(HISTORY_DIR, f"{record_id}.json")
    if not os.path.exists(filename):
        raise HTTPException(status_code=404, detail="历史记录不存在")
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {"success": True, "data": data}
    except Exception as e:
        logger.exception("Get history error")
        raise HTTPException(status_code=500, detail=str(e))
