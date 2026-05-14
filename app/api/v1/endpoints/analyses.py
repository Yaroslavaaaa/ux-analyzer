from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import (
    AnalysisCreate, AnalysisUpdate, AnalysisResponse,
    AnalysisDetailResponse, AnalysisListResponse, AnalysisStatusEnum
)
import uuid

from app.services.project_service import ProjectService

router = APIRouter(prefix="/analyses", tags=["analyses"])

@router.post("/projects/by-slug/{project_slug}", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis_by_slug(
    project_slug: str,
    analysis_data: AnalysisCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    # Сначала находим проект по slug и проверяем владельца
    project_service = ProjectService(db, current_user)
    project = await project_service.get_project_by_slug(project_slug, check_owner=True)
    
    service = AnalysisService(db, current_user)
    analysis = await service.create_analysis(project.id, analysis_data)
    return analysis

@router.get("/{analysis_id}", response_model=AnalysisDetailResponse)
async def get_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает детальную информацию об анализе по ID."""
    service = AnalysisService(db, current_user)
    analysis = await service.get_analysis_by_id(analysis_id)
    
    project = analysis.project
    return {
        **analysis.__dict__,
        "project_name": project.name,
        "owner_username": current_user.username
    }

@router.get("/projects/{project_id}", response_model=AnalysisListResponse)
async def get_project_analyses(
    project_id: uuid.UUID,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AnalysisStatusEnum] = Query(None, description="Фильтр по статусу"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает список анализов проекта с пагинацией и фильтром.
    """
    service = AnalysisService(db, current_user)
    analyses, total = await service.get_project_analyses(
        project_id=project_id,
        skip=skip,
        limit=limit,
        status_filter=status
    )
    return {
        "total": total,
        "analyses": analyses
    }

@router.patch("/{analysis_id}", response_model=AnalysisResponse)
async def update_analysis(
    analysis_id: uuid.UUID,
    update_data: AnalysisUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновляет анализ (статус, UX score, временные метки)."""
    service = AnalysisService(db, current_user)
    analysis = await service.update_analysis(analysis_id, update_data)
    return analysis

@router.delete("/{analysis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Удаляет анализ."""
    service = AnalysisService(db, current_user)
    await service.delete_analysis(analysis_id)
    return None

@router.get("/projects/{project_id}/stats")
async def get_analysis_stats(
    project_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает статистику по анализам проекта.
    """
    service = AnalysisService(db, current_user)
    stats = await service.get_analysis_stats(project_id)
    return stats