from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid
from enum import Enum

class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class ViolationBase(BaseModel):
    metric_id: str = Field(..., max_length=50)
    element_id: Optional[uuid.UUID] = None
    severity: SeverityEnum
    message: str = Field(..., min_length=1)

class ViolationCreate(ViolationBase):
    analysis_id: uuid.UUID

class ViolationResponse(ViolationBase):
    id: uuid.UUID
    analysis_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True

class ViolationDetailResponse(ViolationResponse):
    metric_name: Optional[str] = None
    metric_category: Optional[str] = None
    element_details: Optional[dict] = None  # можно подтянуть поля из Element