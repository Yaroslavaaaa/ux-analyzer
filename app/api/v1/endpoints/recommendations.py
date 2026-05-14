from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.recommendation_service import RecommendationService
from app.schemas.recommendation import RecommendationResponse, RecommendationUpdate
import uuid
from app.services.analysis_service import AnalysisService

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/violation/{violation_id}", response_model=List[RecommendationResponse])
async def get_violation_recommendations(
    violation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Все рекомендации для конкретного нарушения."""
    service = RecommendationService(db, current_user)
    recs = await service.get_recommendations_by_violation(violation_id)
    return recs

@router.get("/{recommendation_id}", response_model=RecommendationResponse)
async def get_recommendation(
    recommendation_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Детали рекомендации."""
    service = RecommendationService(db, current_user)
    rec = await service.get_recommendation(recommendation_id)
    return rec

@router.patch("/{recommendation_id}/vote")
async def vote_recommendation(
    recommendation_id: uuid.UUID,
    vote_data: RecommendationUpdate,  # { "is_helpful": true/false }
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Оценить полезность рекомендации (лайк/дизлайк)."""
    service = RecommendationService(db, current_user)
    rec = await service.vote_helpful(recommendation_id, vote_data.is_helpful)
    return {"message": "Vote recorded", "helpful_votes": rec.helpful_votes}


@router.get("/analysis/{analysis_id}")
async def get_recommendations_by_analysis(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Получить все рекомендации для всех нарушений данного анализа."""
    from app.services.analysis_service import AnalysisService
    analysis_service = AnalysisService(db, current_user)
    await analysis_service.get_analysis_by_id(analysis_id)
    
    from app.models.recommendation import Recommendation
    from app.models.violation import Violation
    from sqlalchemy import select
    
    stmt = (
        select(Recommendation)
        .join(Violation, Recommendation.violation_id == Violation.id)
        .where(Violation.analysis_id == analysis_id)
        .order_by(Recommendation.created_at.desc())
    )
    result = await db.execute(stmt)
    recommendations = result.scalars().all()
    return recommendations