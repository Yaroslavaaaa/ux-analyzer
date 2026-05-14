from pydantic import BaseModel, Field, HttpUrl, validator
from datetime import datetime
from typing import Optional
import uuid
from enum import Enum

class AnalysisStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class AnalysisBase(BaseModel):
    url: str = Field(..., max_length=500, description="URL анализируемой страницы")

class AnalysisCreate(AnalysisBase):
    pass

class AnalysisUpdate(BaseModel):
    status: Optional[AnalysisStatusEnum] = None
    ux_score: Optional[float] = Field(None, ge=0, le=100)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class AnalysisResponse(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    url: str
    status: AnalysisStatusEnum
    ux_score: Optional[float]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class AnalysisDetailResponse(AnalysisResponse):
    """Детальный ответ с дополнительной информацией (например, владелец проекта)"""
    project_name: str
    owner_username: str

class AnalysisListResponse(BaseModel):
    total: int
    analyses: list[AnalysisResponse]