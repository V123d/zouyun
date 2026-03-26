from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from ..database import AsyncSessionLocal
from ..models.standard_quota import StandardQuota
from ..schemas.standard_quota_schema import StandardQuotaCreate, StandardQuotaUpdate, StandardQuotaRead
from typing import List

router = APIRouter(prefix="/api/standard-quotas", tags=["灶别标准"])

@router.get("/", response_model=List[StandardQuotaRead])
async def get_all_quotas():
    """获取所有灶别标准"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(StandardQuota))
        return result.scalars().all()

@router.post("/", response_model=StandardQuotaRead, status_code=status.HTTP_201_CREATED)
async def create_quota(quota_in: StandardQuotaCreate):
    """创建新灶别标准"""
    async with AsyncSessionLocal() as session:
        # 检查是否已存在同类型的标准
        result = await session.execute(select(StandardQuota).where(StandardQuota.class_type == quota_in.class_type))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="Standard for this class already exists")
        
        new_quota = StandardQuota(**quota_in.dict())
        session.add(new_quota)
        await session.commit()
        await session.refresh(new_quota)
        return new_quota

@router.put("/{quota_id}", response_model=StandardQuotaRead)
async def update_quota(quota_id: int, quota_in: StandardQuotaUpdate):
    """更新灶别标准"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(StandardQuota).where(StandardQuota.id == quota_id))
        quota = result.scalar_one_or_none()
        if not quota:
            raise HTTPException(status_code=404, detail="Standard quota not found")
        
        update_data = quota_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(quota, key, value)
        
        session.add(quota)
        await session.commit()
        await session.refresh(quota)
        return quota

@router.delete("/{quota_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_quota(quota_id: int):
    """删除灶别标准"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(StandardQuota).where(StandardQuota.id == quota_id))
        quota = result.scalar_one_or_none()
        if not quota:
            raise HTTPException(status_code=404, detail="Standard quota not found")
        
        await session.delete(quota)
        await session.commit()
        return None
