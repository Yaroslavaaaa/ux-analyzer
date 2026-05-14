from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class ScoreBase(BaseModel):
    category: str = Field(..., max_length=100)
    score: float = Field(..., ge=0, le=100)
    weight: float = Field(1.0, ge=0, le=10)

class ScoreCreate(ScoreBase):
    analysis_id: uuid.UUID

class ScoreUpdate(BaseModel):
    score: Optional[float] = Field(None, ge=0, le=100)
    weight: Optional[float] = Field(None, ge=0, le=10)
    details: Optional[Dict[str, Any]] = None

class ScoreResponse(ScoreBase):
    id: uuid.UUID
    analysis_id: uuid.UUID
    details: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True