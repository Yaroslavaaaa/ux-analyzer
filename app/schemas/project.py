from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, Dict, Any
import re

# Базовые схемы
class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255, description="Название проекта")
    slug: Optional[str] = Field(None, min_length=1, max_length=255, description="URL-friendly имя (генерируется автоматически)")
    description: Optional[str] = Field(None, max_length=1000, description="Описание проекта")
    base_url: Optional[str] = Field(None, max_length=500, description="Базовый URL сайта")
    is_public: bool = Field(False, description="Публичный ли проект")
    extra_data: Optional[Dict[str, Any]] = Field(None, description="Дополнительные данные")

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    """Обновление проекта (все поля опциональны)"""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    base_url: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None
    is_public: Optional[bool] = None
    extra_data: Optional[Dict[str, Any]] = None

class ProjectResponse(BaseModel):
    """Ответ с данными проекта (без ID)"""
    slug: str
    name: str
    description: Optional[str]
    base_url: Optional[str]
    is_active: bool
    is_public: bool
    owner_username: str
    created_at: datetime
    updated_at: datetime
    analyses_count: int = 0
    
    class Config:
        from_attributes = True

class ProjectDetailResponse(ProjectResponse):
    """Детальный ответ с дополнительной информацией"""
    extra_data: Optional[Dict[str, Any]] = None
    last_analysis_at: Optional[datetime] = None

class ProjectListResponse(BaseModel):
    """Ответ со списком проектов"""
    total: int
    projects: list[ProjectResponse]

# Валидаторы
def validate_slug(slug: str) -> str:
    """Валидация slug"""
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    if not re.match(pattern, slug):
        raise ValueError('Slug must contain only lowercase letters, numbers, and hyphens')
    return slug

def slugify(text: str) -> str:
    """Преобразует текст в slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text.strip('-')