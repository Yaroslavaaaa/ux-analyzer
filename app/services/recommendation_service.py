from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.analysis import Analysis
from app.models.project import Project
from app.models.user import User
from app.models.violation import Violation
from app.models.recommendation import Recommendation
from app.schemas.recommendation import RecommendationCreate
import uuid

class RecommendationService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def _check_violation_access(self, violation_id: uuid.UUID) -> Violation:
        """Проверяет, что нарушение принадлежит анализу пользователя"""
        result = await self.db.execute(
            select(Violation)
            .where(Violation.id == violation_id)
            .join(Violation.analysis)
            .join(Analysis.project)
            .where(Project.user_id == self.current_user.id)
        )
        violation = result.scalar_one_or_none()
        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Violation not found or access denied"
            )
        return violation
    
    async def create_recommendation(self, rec_data: RecommendationCreate) -> Recommendation:
        """Создаёт рекомендацию для нарушения (вызывается LLM)"""
        await self._check_violation_access(rec_data.violation_id)
        rec = Recommendation(
            violation_id=rec_data.violation_id,
            text=rec_data.text
        )
        self.db.add(rec)
        await self.db.commit()
        await self.db.refresh(rec)
        return rec
    
    async def get_recommendations_by_violation(self, violation_id: uuid.UUID) -> List[Recommendation]:
        """Получает все рекомендации для нарушения"""
        await self._check_violation_access(violation_id)
        result = await self.db.execute(
            select(Recommendation).where(Recommendation.violation_id == violation_id)
        )
        return result.scalars().all()


    # Добавьте в класс RecommendationService:

    async def create_recommendation_for_violation(self, violation_id: uuid.UUID, text: str) -> Recommendation:
        """Внутренний метод для создания рекомендации (без проверки прав)."""
        rec = Recommendation(
            violation_id=violation_id,
            text=text,
            is_helpful=False,
            helpful_votes=0
        )
        self.db.add(rec)
        await self.db.commit()
        await self.db.refresh(rec)
        return rec
    
    async def vote_helpful(self, recommendation_id: uuid.UUID, is_helpful: bool) -> Recommendation:
        """Оценить рекомендацию (помогла/не помогла)"""
        rec = await self.get_recommendation(recommendation_id)
        rec.is_helpful = is_helpful
        rec.helpful_votes += 1
        await self.db.commit()
        await self.db.refresh(rec)
        return rec
    
    async def get_recommendation(self, recommendation_id: uuid.UUID) -> Recommendation:
        """Получить рекомендацию по ID с проверкой доступа"""
        result = await self.db.execute(
            select(Recommendation).where(Recommendation.id == recommendation_id)
        )
        rec = result.scalar_one_or_none()
        if not rec:
            raise HTTPException(status_code=404, detail="Recommendation not found")
        await self._check_violation_access(rec.violation_id)
        return rec

    