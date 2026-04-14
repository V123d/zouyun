from pydantic import BaseModel, Field
from typing import Dict, Optional


class StandardQuotaBase(BaseModel):
    class_type: str = Field(..., description="配置文件唯一标识，如幼儿园大班")
    name: str = Field(default="", description="配置文件显示名称")
    description: str = Field(default="", description="配置文件描述说明")
    quotas: Dict[str, float] = Field(..., description="各项食材的定量标准（克/人/天）或营养素标准")
    quota_type: str = Field(default="nutrition", description="配额类型：nutrition=营养素配额")
    is_system: bool = Field(default=False, description="是否为系统内置（内置不可删除）")


class StandardQuotaCreate(StandardQuotaBase):
    pass


class StandardQuotaUpdate(BaseModel):
    class_type: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    quotas: Optional[Dict[str, float]] = None
    quota_type: Optional[str] = None


class StandardQuotaRead(StandardQuotaBase):
    id: int

    class Config:
        from_attributes = True
