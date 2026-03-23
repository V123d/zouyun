import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..services.constraint_checker import _check_menu
from ..database import get_db
from ..security import get_current_active_user
from ..models.user import User
from ..models.history import MenuHistory

router = APIRouter(prefix="/api/menu", tags=["菜单管理"])

logger = logging.getLogger(__name__)

class RecalculateRequest(BaseModel):
    menu: Dict[str, Any]
    config: Dict[str, Any]

@router.post("/recalculate")
async def recalculate_menu(
    req: RecalculateRequest,
    current_user: User = Depends(get_current_active_user)
):
    """重新计算检查"""
    try:
        result = await _check_menu(req.menu, req.config)
        final_alerts = [
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
                "alerts": final_alerts
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
async def save_history(
    req: SaveHistoryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """保存当前完整排餐结果至用户的历史记录"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    record_id = f"plan_{timestamp}_{current_user.username}"
    
    new_record = MenuHistory(
        id=record_id,
        user_id=current_user.id,
        name=req.name or f"排餐方案 {datetime.now().strftime('%m-%d %H:%M')}",
        menu_data=req.menu,
        metrics_data=req.metrics,
        config_data=req.config
    )
    
    db.add(new_record)
    await db.commit()
    
    return {"success": True, "id": record_id, "message": "保存成功"}


@router.get("/history")
async def list_history(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """列出当前用户的所有历史排餐记录元信息"""
    try:
        res = await db.execute(
            select(MenuHistory)
            .where(MenuHistory.user_id == current_user.id)
            .order_by(MenuHistory.created_at.desc())
        )
        histories = res.scalars().all()
        
        records = [{
            "id": h.id,
            "name": h.name,
            "timestamp": h.created_at.isoformat() if h.created_at else None,
            "metrics": h.metrics_data
        } for h in histories]
        
        return {"success": True, "records": records}
    except Exception as e:
        logger.exception("List history error")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history/{record_id}")
async def get_history(
    record_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取当前用户单条历史记录的详情内容"""
    try:
        res = await db.execute(
            select(MenuHistory)
            .where(MenuHistory.id == record_id)
            .where(MenuHistory.user_id == current_user.id)
        )
        record = res.scalars().first()
        
        if not record:
            raise HTTPException(status_code=404, detail="历史记录不存在或无权限访问")
            
        data = {
            "id": record.id,
            "name": record.name,
            "timestamp": record.created_at.isoformat() if record.created_at else None,
            "menu": record.menu_data,
            "metrics": record.metrics_data,
            "config": record.config_data
        }
        return {"success": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Get history error")
        raise HTTPException(status_code=500, detail=str(e))
