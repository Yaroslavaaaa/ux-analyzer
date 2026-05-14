from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.violation_service import ViolationService
from app.schemas.violation import ViolationResponse, ViolationDetailResponse
import uuid

router = APIRouter(prefix="/violations", tags=["violations"])

@router.get("/analysis/{analysis_id}", response_model=List[ViolationResponse])
async def get_analysis_violations(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает все нарушения для конкретного анализа."""
    service = ViolationService(db, current_user)
    violations = await service.get_violations_by_analysis(analysis_id)
    return violations

@router.get("/{violation_id}", response_model=ViolationDetailResponse)
async def get_violation(
    violation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получает нарушение по ID с деталями метрики и элемента."""
    service = ViolationService(db, current_user)
    violation = await service.get_violation(violation_id)
    
    # Дополнительная информация
    metric = violation.metric_definition
    element = violation.element
    
    return {
        **violation.__dict__,
        "metric_name": metric.name if metric else None,
        "metric_category": metric.category if metric else None,
        "element_details": {
            "element_type": element.element_type,
            "text": element.text,
            "x": element.x,
            "y": element.y,
            "width": element.width,
            "height": element.height,
            "is_above_fold": element.is_above_fold
        } if element else None
    }