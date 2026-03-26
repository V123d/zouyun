from pydantic import BaseModel, Field
from typing import Dict, Optional

class StandardQuotaBase(BaseModel):
    class_type: str = Field(..., description="灶别：一类灶、二类灶、三类灶")
    quotas: Dict[str, float] = Field(..., description="各项食材的定量标准")

class StandardQuotaCreate(StandardQuotaBase):
    pass

class StandardQuotaUpdate(BaseModel):
    class_type: Optional[str] = None
    quotas: Optional[Dict[str, float]] = None

class StandardQuotaRead(StandardQuotaBase):
    id: int

    class Config:
        from_attributes = True
