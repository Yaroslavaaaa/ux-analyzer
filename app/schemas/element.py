from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

class ElementBase(BaseModel):
    element_type: str = Field(..., max_length=50)
    text: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    is_above_fold: bool = False
    font_size: Optional[int] = None
    contrast_ratio: Optional[float] = Field(None, ge=1, le=21)
    has_alt: bool = False
    has_label: bool = False

class ElementCreate(ElementBase):
    page_id: uuid.UUID

class ElementUpdate(BaseModel):
    element_type: Optional[str] = None
    text: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    width: Optional[float] = None
    height: Optional[float] = None
    is_above_fold: Optional[bool] = None
    font_size: Optional[int] = None
    contrast_ratio: Optional[float] = None
    has_alt: Optional[bool] = None
    has_label: Optional[bool] = None

class ElementResponse(ElementBase):
    id: uuid.UUID
    page_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True