from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

class MetricValueBase(BaseModel):
    value: float = Field(..., ge=0.0, le=100.0)
    raw_data: Optional[Dict[str, Any]] = None

class MetricValueCreate(MetricValueBase):
    analysis_id: uuid.UUID
    metric_id: str

class MetricValueResponse(MetricValueBase):
    id: uuid.UUID
    analysis_id: uuid.UUID
    metric_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True