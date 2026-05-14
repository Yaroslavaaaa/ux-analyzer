from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.element_service import ElementService
from app.schemas.element import ElementResponse
import uuid

router = APIRouter(prefix="/elements", tags=["elements"])

@router.get("/page/{page_id}", response_model=List[ElementResponse])
async def get_page_elements(
    page_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает все нарушающие элементы для указанной страницы."""
    service = ElementService(db, current_user)
    elements = await service.get_elements_by_page(page_id)
    return elements

@router.get("/{element_id}", response_model=ElementResponse)
async def get_element(
    element_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает элемент по ID."""
    service = ElementService(db, current_user)
    element = await service.get_element(element_id)
    return element