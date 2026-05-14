from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional
import uuid

class PageBase(BaseModel):
    url: str = Field(..., max_length=500)
    page_height: Optional[int] = None
    viewport_height: Optional[int] = None
    scroll_depth_ratio: Optional[float] = Field(None, ge=0, le=1)
    screenshot_url: Optional[str] = None

class PageCreate(PageBase):
    analysis_id: uuid.UUID

class PageUpdate(BaseModel):
    page_height: Optional[int] = None
    viewport_height: Optional[int] = None
    scroll_depth_ratio: Optional[float] = None
    screenshot_url: Optional[str] = None

class PageResponse(PageBase):
    id: uuid.UUID
    analysis_id: uuid.UUID
    created_at: datetime
    
    class Config:
        from_attributes = True