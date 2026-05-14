from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class RecommendationBase(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)

class RecommendationCreate(RecommendationBase):
    violation_id: uuid.UUID

class RecommendationUpdate(BaseModel):
    text: Optional[str] = None
    is_helpful: Optional[bool] = None

class RecommendationResponse(RecommendationBase):
    id: uuid.UUID
    violation_id: uuid.UUID
    is_helpful: bool
    helpful_votes: int
    created_at: datetime
    
    class Config:
        from_attributes = True