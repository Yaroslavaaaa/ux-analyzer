from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from typing import Optional, List
from app.models.project import Project
from app.models.user import User
from app.models.analysis import Analysis
from app.models.page import Page
from app.schemas.page import PageCreate, PageUpdate
import uuid
import os
from pathlib import Path

class PageService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def _check_analysis_access(self, analysis_id: uuid.UUID) -> Analysis:
        """Проверяет, что анализ принадлежит проекту пользователя"""
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .join(Analysis.project)
            .where(Project.user_id == self.current_user.id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found or access denied"
            )
        return analysis
    
    async def create_page(self, page_data: PageCreate) -> Page:
        """Создаёт страницу для анализа (обычно вызывается автоматически)"""
        # Проверяем доступ к анализу
        await self._check_analysis_access(page_data.analysis_id)
        
        page = Page(
            analysis_id=page_data.analysis_id,
            url=page_data.url,
            page_height=page_data.page_height,
            viewport_height=page_data.viewport_height,
            scroll_depth_ratio=page_data.scroll_depth_ratio,
            screenshot_url=page_data.screenshot_url
        )
        self.db.add(page)
        await self.db.commit()
        await self.db.refresh(page)
        return page
    
    async def get_pages_by_analysis(self, analysis_id: uuid.UUID) -> List[Page]:
        """Получает все страницы анализа"""
        await self._check_analysis_access(analysis_id)
        result = await self.db.execute(
            select(Page).where(Page.analysis_id == analysis_id)
        )
        return result.scalars().all()
    
    async def get_page(self, page_id: uuid.UUID) -> Page:
        """Получает страницу по ID с проверкой доступа"""
        result = await self.db.execute(
            select(Page).where(Page.id == page_id)
        )
        page = result.scalar_one_or_none()
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        # Проверяем доступ через анализ
        await self._check_analysis_access(page.analysis_id)
        return page
    
    async def update_page(self, page_id: uuid.UUID, update_data: PageUpdate) -> Page:
        """Обновляет данные страницы (высота, скролл, URL скриншота)"""
        page = await self.get_page(page_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            if hasattr(page, field) and value is not None:
                setattr(page, field, value)
        
        await self.db.commit()
        await self.db.refresh(page)
        return page
    
    async def save_screenshot(self, page_id: uuid.UUID, file_content: bytes, filename: str) -> str:
        """
        Сохраняет скриншот на диск и возвращает URL.
        В будущем можно заменить на S3 или облачное хранилище.
        """
        page = await self.get_page(page_id)
        
        # Создаём директорию для скриншотов, если её нет
        screenshots_dir = Path("static/screenshots")
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        
        # Генерируем уникальное имя файла
        ext = filename.split('.')[-1] if '.' in filename else 'png'
        safe_filename = f"{page_id}_{page.analysis_id}.{ext}"
        file_path = screenshots_dir / safe_filename
        
        # Сохраняем файл
        with open(file_path, "wb") as f:
            f.write(file_content)
        
        # Формируем URL для доступа (через статику)
        url = f"/static/screenshots/{safe_filename}"
        
        # Обновляем запись в БД
        page.screenshot_url = url
        await self.db.commit()
        
        return url