from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.score_service import ScoreService
from app.schemas.score import ScoreResponse
import uuid

router = APIRouter(prefix="/scores", tags=["scores"])

@router.get("/analysis/{analysis_id}", response_model=List[ScoreResponse])
async def get_analysis_scores(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все агрегированные оценки для анализа"""
    service = ScoreService(db, current_user)
    scores = await service.get_scores_by_analysis(analysis_id)
    return scores

@router.post("/analysis/{analysis_id}/calculate")
async def calculate_scores(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Принудительно пересчитать и сохранить оценки категорий для анализа"""
    service = ScoreService(db, current_user)
    scores = await service.calculate_all_scores(analysis_id)
    return {"message": f"Scores calculated for {len(scores)} categories"}