from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.user import User
from app.models.analysis import Analysis
from app.models.page import Page
from app.models.element import Element
from app.schemas.element import ElementCreate, ElementUpdate
import uuid

class ElementService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def _check_page_access(self, page_id: uuid.UUID) -> Page:
        """Проверяет, что страница принадлежит анализу пользователя"""
        result = await self.db.execute(
            select(Page)
            .where(Page.id == page_id)
            .join(Page.analysis)
            .join(Analysis.project)
            .where(Project.user_id == self.current_user.id)
        )
        page = result.scalar_one_or_none()
        if not page:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Page not found or access denied"
            )
        return page
    
    async def create_element(self, element_data: ElementCreate) -> Element:
        """Сохраняет нарушающий элемент (вызывается во время анализа)"""
        # Проверяем доступ к странице
        await self._check_page_access(element_data.page_id)
        
        element = Element(
            page_id=element_data.page_id,
            element_type=element_data.element_type,
            text=element_data.text,
            x=element_data.x,
            y=element_data.y,
            width=element_data.width,
            height=element_data.height,
            is_above_fold=element_data.is_above_fold,
            font_size=element_data.font_size,
            contrast_ratio=element_data.contrast_ratio,
            has_alt=element_data.has_alt,
            has_label=element_data.has_label
        )
        self.db.add(element)
        await self.db.commit()
        await self.db.refresh(element)
        return element
    
    async def get_elements_by_page(self, page_id: uuid.UUID) -> List[Element]:
        """Получает все нарушающие элементы страницы"""
        await self._check_page_access(page_id)
        result = await self.db.execute(
            select(Element).where(Element.page_id == page_id)
        )
        return result.scalars().all()
    
    async def get_element(self, element_id: uuid.UUID) -> Element:
        """Получает элемент по ID с проверкой прав"""
        result = await self.db.execute(
            select(Element).where(Element.id == element_id)
        )
        element = result.scalar_one_or_none()
        if not element:
            raise HTTPException(status_code=404, detail="Element not found")
        await self._check_page_access(element.page_id)
        return element
    
    async def delete_element(self, element_id: uuid.UUID) -> None:
        """Удаляет элемент (обычно не нужно, но на всякий случай)"""
        element = await self.get_element(element_id)
        await self.db.delete(element)
        await self.db.commit()