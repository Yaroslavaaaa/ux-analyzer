from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid
from enum import Enum

class SeverityEnum(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class OverlayBase(BaseModel):
    x: float
    y: float
    width: float = Field(..., gt=0)
    height: float = Field(..., gt=0)
    severity: SeverityEnum
    color: Optional[str] = Field(None, pattern=r'^#[0-9a-fA-F]{6}$')
    tooltip: Optional[str] = Field(None, max_length=500)

class OverlayCreate(OverlayBase):
    analysis_id: uuid.UUID
    element_id: Optional[uuid.UUID] = None

class OverlayUpdate(BaseModel):
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    severity: Optional[SeverityEnum] = None
    color: Optional[str] = None
    tooltip: Optional[str] = None

class OverlayResponse(OverlayBase):
    id: uuid.UUID
    analysis_id: uuid.UUID
    element_id: Optional[uuid.UUID]
    color: Optional[str]
    tooltip: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True