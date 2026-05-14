from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.analysis import Analysis, AnalysisStatus
from app.models.page import Page
from app.models.user import User
from app.services.project_service import ProjectService
from app.schemas.project import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    ProjectDetailResponse, ProjectListResponse
)
from app.services.analysis_service import AnalysisService
from app.schemas.analysis import (
    AnalysisCreate, AnalysisResponse, AnalysisListResponse, 
    AnalysisStatusEnum
)
from app.tasks.collector_task import collect_page_data

router = APIRouter(prefix="/projects", tags=["projects"])

# Все эндпоинты проектов требуют авторизации
@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Создание нового проекта для текущего пользователя
    
    - **name**: Название проекта (обязательно)
    - **slug**: Уникальный идентификатор (опционально, генерируется из name)
    - **description**: Описание проекта
    - **base_url**: Базовый URL сайта
    - **is_public**: Публичный ли проект
    """
    service = ProjectService(db, current_user)
    project = await service.create_project(project_data)
    
    # Формируем ответ
    return {
        "slug": project.slug,
        "name": project.name,
        "description": project.description,
        "base_url": project.base_url,
        "is_active": project.is_active,
        "is_public": project.is_public,
        "owner_username": current_user.username,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "analyses_count": 0
    }

@router.get("", response_model=ProjectListResponse)
async def get_user_projects(
    skip: int = Query(0, ge=0, description="Количество пропускаемых записей"),
    limit: int = Query(100, ge=1, le=1000, description="Максимальное количество записей"),
    include_inactive: bool = Query(False, description="Включать неактивные проекты"),
    only_public: bool = Query(False, description="Только публичные проекты"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка всех проектов текущего пользователя с пагинацией
    """
    service = ProjectService(db, current_user)
    projects, total = await service.get_user_projects(
        skip=skip,
        limit=limit,
        include_inactive=include_inactive,
        only_public=only_public
    )
    
    # Формируем ответ
    projects_response = [
        {
            "slug": p.slug,
            "name": p.name,
            "description": p.description,
            "base_url": p.base_url,
            "is_active": p.is_active,
            "is_public": p.is_public,
            "owner_username": current_user.username,
            "created_at": p.created_at,
            "updated_at": p.updated_at,
            "analyses_count": 0  # TODO: добавить из анализа
        }
        for p in projects
    ]
    
    return {
        "total": total,
        "projects": projects_response
    }

@router.get("/{slug}", response_model=ProjectDetailResponse)
async def get_project(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение детальной информации о проекте по slug
    """
    service = ProjectService(db, current_user)
    project = await service.get_project_by_slug(slug)
    
    # Получаем статистику
    stats = await service.get_project_stats(slug)
    
    return {
        "slug": project.slug,
        "name": project.name,
        "description": project.description,
        "base_url": project.base_url,
        "is_active": project.is_active,
        "is_public": project.is_public,
        "owner_username": current_user.username,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "analyses_count": stats.get("total_analyses", 0),
        "extra_data": project.extra_data,
        "last_analysis_at": stats.get("last_analysis_at")
    }

@router.patch("/{slug}", response_model=ProjectResponse)
async def update_project(
    slug: str,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Обновление информации о проекте
    
    Можно обновлять любое количество полей
    """
    service = ProjectService(db, current_user)
    project = await service.update_project(slug, update_data)
    
    return {
        "slug": project.slug,
        "name": project.name,
        "description": project.description,
        "base_url": project.base_url,
        "is_active": project.is_active,
        "is_public": project.is_public,
        "owner_username": current_user.username,
        "created_at": project.created_at,
        "updated_at": project.updated_at,
        "analyses_count": 0
    }

@router.delete("/{slug}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    slug: str,
    hard_delete: bool = Query(False, description="Полное удаление (иначе soft delete)"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Удаление проекта
    
    - По умолчанию: soft delete (проект становится неактивным)
    - hard_delete=true: полное удаление из БД
    """
    service = ProjectService(db, current_user)
    await service.delete_project(slug, soft_delete=not hard_delete)
    return None

@router.get("/check-slug/{slug}")
async def check_slug_availability(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Проверка доступности slug перед созданием проекта
    """
    service = ProjectService(db, current_user)
    return await service.check_slug_availability(slug)

@router.get("/{slug}/stats")
async def get_project_stats(
    slug: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение статистики по проекту
    """
    service = ProjectService(db, current_user)
    return await service.get_project_stats(slug)




@router.get("/{project_slug}/analyses", response_model=AnalysisListResponse)
async def get_project_analyses(
    project_slug: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[AnalysisStatusEnum] = Query(None, description="Фильтр по статусу"),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает список анализов проекта по его slug.
    """
    # Находим проект
    project_service = ProjectService(db, current_user)
    project = await project_service.get_project_by_slug(project_slug, check_owner=True)
    
    # Получаем анализы
    analysis_service = AnalysisService(db, current_user)
    analyses, total = await analysis_service.get_project_analyses(
        project_id=project.id,
        skip=skip,
        limit=limit,
        status_filter=status
    )
    return {
        "total": total,
        "analyses": analyses
    }

@router.get("/{project_slug}/analyses/stats")
async def get_project_analyses_stats(
    project_slug: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Получает статистику по анализам проекта.
    """
    project_service = ProjectService(db, current_user)
    project = await project_service.get_project_by_slug(project_slug, check_owner=True)
    
    analysis_service = AnalysisService(db, current_user)
    stats = await analysis_service.get_analysis_stats(project.id)
    return stats

@router.post("/{project_slug}/analyses", response_model=AnalysisResponse, status_code=status.HTTP_201_CREATED)
async def create_project_analysis(
    project_slug: str,
    analysis_data: AnalysisCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    project_service = ProjectService(db, current_user)
    project = await project_service.get_project_by_slug(project_slug, check_owner=True)

    analysis = Analysis(
        project_id=project.id,
        url=analysis_data.url,
        status=AnalysisStatus.PENDING
    )
    db.add(analysis)
    await db.commit()
    await db.refresh(analysis)

    # Создаём страницу (пока без данных)
    page = Page(
        analysis_id=analysis.id,
        url=analysis_data.url
    )
    db.add(page)
    await db.commit()
    await db.refresh(page)

    # Запускаем фоновую задачу сбора данных
    background_tasks.add_task(
        collect_page_data,
        analysis_id=analysis.id,
        page_id=page.id,
        url=analysis_data.url
    )

    return analysis