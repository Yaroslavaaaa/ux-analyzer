from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from typing import Optional, List
from app.models.user import User
from app.models.project import Project
from app.schemas.project import ProjectCreate, ProjectUpdate, slugify
import uuid

class ProjectService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def create_project(self, project_data: ProjectCreate) -> Project:
        """Создание нового проекта для текущего пользователя"""
        
        # Генерируем slug если не указан
        slug = project_data.slug or slugify(project_data.name)
        
        # Проверяем уникальность slug
        existing = await self.db.execute(
            select(Project).where(Project.slug == slug)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Project with slug '{slug}' already exists"
            )
        
        # Создаем проект
        project = Project(
            user_id=self.current_user.id,
            name=project_data.name,
            slug=slug,
            description=project_data.description,
            base_url=project_data.base_url,
            is_public=project_data.is_public,
            extra_data=project_data.extra_data or {}
        )
        
        self.db.add(project)
        await self.db.commit()
        await self.db.refresh(project)
        
        return project
    
    async def get_user_projects(
        self, 
        skip: int = 0, 
        limit: int = 100,
        include_inactive: bool = False,
        only_public: bool = False
    ) -> tuple[List[Project], int]:
        """Получение списка проектов пользователя с пагинацией"""
        
        # Базовый запрос
        query = select(Project).where(Project.user_id == self.current_user.id)
        
        # Фильтры
        if not include_inactive:
            query = query.where(Project.is_active == True)
        
        if only_public:
            query = query.where(Project.is_public == True)
        
        # Получаем общее количество
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Пагинация
        query = query.offset(skip).limit(limit).order_by(Project.created_at.desc())
        
        result = await self.db.execute(query)
        projects = result.scalars().all()
        
        return projects, total or 0
    
    async def get_project_by_slug(self, slug: str, check_owner: bool = False) -> Project:
        """Получение проекта по slug"""
        
        query = select(Project).where(Project.slug == slug)
        
        # Если нужно проверить владельца
        if check_owner:
            query = query.where(Project.user_id == self.current_user.id)
        
        result = await self.db.execute(query)
        project = result.scalar_one_or_none()
        
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found"
            )
        
        # Проверяем доступ (если проект не публичный и не владелец)
        if not project.is_public and not check_owner:
            if project.user_id != self.current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project"
                )
        
        return project
    
    async def update_project(
        self, 
        slug: str, 
        update_data: ProjectUpdate
    ) -> Project:
        """Обновление проекта"""
        
        # Находим проект
        project = await self.get_project_by_slug(slug, check_owner=True)
        
        # Обновляем поля
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Если обновляем name, обновляем и slug
        if "name" in update_dict and update_dict["name"]:
            new_slug = slugify(update_dict["name"])
            if new_slug != project.slug:
                # Проверяем уникальность нового slug
                existing = await self.db.execute(
                    select(Project).where(
                        and_(
                            Project.slug == new_slug,
                            Project.id != project.id
                        )
                    )
                )
                if existing.scalar_one_or_none():
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Project with slug '{new_slug}' already exists"
                    )
                project.slug = new_slug
        
        for field, value in update_dict.items():
            if hasattr(project, field) and value is not None:
                setattr(project, field, value)
        
        await self.db.commit()
        await self.db.refresh(project)
        
        return project
    
    async def delete_project(self, slug: str, soft_delete: bool = True) -> bool:
        """Удаление проекта (soft или hard delete)"""
        
        project = await self.get_project_by_slug(slug, check_owner=True)
        
        if soft_delete:
            # Soft delete - просто деактивируем
            project.is_active = False
            await self.db.commit()
            return True
        else:
            # Hard delete - удаляем полностью
            await self.db.delete(project)
            await self.db.commit()
            return True
    
    async def get_project_stats(self, slug: str) -> dict:
        """Получение статистики по проекту"""
        
        project = await self.get_project_by_slug(slug, check_owner=True)
        
        # Здесь позже добавим статистику из analyses
        return {
            "total_analyses": 0,  # TODO: добавить из анализа
            "last_analysis_at": None,
            "average_ux_score": None
        }
    
    async def check_slug_availability(self, slug: str) -> dict:
        """Проверка доступности slug"""
        
        existing = await self.db.execute(
            select(Project).where(Project.slug == slug)
        )
        is_available = existing.scalar_one_or_none() is None
        
        return {
            "slug": slug,
            "is_available": is_available,
            "message": "Slug is available" if is_available else "Slug already taken"
        }