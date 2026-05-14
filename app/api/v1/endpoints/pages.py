from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.page_service import PageService
from app.schemas.page import PageResponse, PageUpdate
import uuid

router = APIRouter(prefix="/pages", tags=["pages"])

@router.get("/analysis/{analysis_id}", response_model=List[PageResponse])
async def get_analysis_pages(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает все страницы, принадлежащие анализу."""
    service = PageService(db, current_user)
    pages = await service.get_pages_by_analysis(analysis_id)
    return pages

@router.get("/{page_id}", response_model=PageResponse)
async def get_page(
    page_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает страницу по ID."""
    service = PageService(db, current_user)
    page = await service.get_page(page_id)
    return page

@router.patch("/{page_id}", response_model=PageResponse)
async def update_page(
    page_id: uuid.UUID,
    update_data: PageUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Обновляет данные страницы (высота, скролл)."""
    service = PageService(db, current_user)
    page = await service.update_page(page_id, update_data)
    return page

@router.post("/{page_id}/screenshot", status_code=status.HTTP_200_OK)
async def upload_screenshot(
    page_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Загружает скриншот для страницы.
    Принимает файл изображения, сохраняет на диск, обновляет screenshot_url.
    """
    # Читаем содержимое файла
    contents = await file.read()
    
    service = PageService(db, current_user)
    url = await service.save_screenshot(page_id, contents, file.filename)
    
    return {"screenshot_url": url}