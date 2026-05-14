from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from typing import List, Dict
from app.models.user import User
from app.models.analysis import Analysis
from app.models.metric_definition import MetricDefinition
from app.models.score import Score
from app.schemas.score import ScoreCreate, ScoreUpdate
from app.models.project import Project
import uuid

class ScoreService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def _check_analysis_access(self, analysis_id: uuid.UUID) -> Analysis:
        result = await self.db.execute(
            select(Analysis)
            .where(Analysis.id == analysis_id)
            .join(Analysis.project)
            .where(Project.user_id == self.current_user.id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        return analysis
    
    async def calculate_category_score(self, analysis_id: uuid.UUID, category: str) -> float:
        """
        Рассчитывает агрегированную оценку для категории на основе значений метрик.
        Формула: взвешенное среднее метрик категории.
        """
        # Запрос к metric_values, соединённый с metric_definitions
        result = await self.db.execute(
            select(
                MetricDefinition.weight,
                MetricValue.value
            )
            .join(MetricValue, MetricDefinition.id == MetricValue.metric_id)
            .where(
                and_(
                    MetricValue.analysis_id == analysis_id,
                    MetricDefinition.category == category
                )
            )
        )
        metrics = result.all()
        
        if not metrics:
            return 0.0
        
        total_weight = sum(m.weight for m in metrics)
        if total_weight == 0:
            return 0.0
        
        weighted_sum = sum(m.weight * m.value for m in metrics)
        score = (weighted_sum / total_weight) * 100  # нормализуем в 0-100
        return round(score, 2)
    
    async def save_category_score(self, analysis_id: uuid.UUID, category: str) -> Score:
        """Рассчитывает и сохраняет оценку категории"""
        score_value = await self.calculate_category_score(analysis_id, category)
        
        # Проверяем, существует ли уже запись
        existing = await self.db.execute(
            select(Score).where(
                and_(
                    Score.analysis_id == analysis_id,
                    Score.category == category
                )
            )
        )
        score_obj = existing.scalar_one_or_none()
        
        if score_obj:
            score_obj.score = score_value
            score_obj.updated_at = func.now()
        else:
            score_obj = Score(
                analysis_id=analysis_id,
                category=category,
                score=score_value
            )
            self.db.add(score_obj)
        
        await self.db.commit()
        await self.db.refresh(score_obj)
        return score_obj
    
    async def calculate_all_scores(self, analysis_id: uuid.UUID) -> List[Score]:
        """Рассчитывает и сохраняет оценки для всех категорий, присутствующих в метриках анализа"""
        await self._check_analysis_access(analysis_id)
        
        # Получаем уникальные категории метрик, которые есть в analysis
        result = await self.db.execute(
            select(MetricDefinition.category)
            .join(MetricValue, MetricDefinition.id == MetricValue.metric_id)
            .where(MetricValue.analysis_id == analysis_id)
            .distinct()
        )
        categories = result.scalars().all()
        
        scores = []
        for category in categories:
            score = await self.save_category_score(analysis_id, category)
            scores.append(score)
        
        # Также обновим общий UX Score в Analysis
        total_score = sum(s.score * s.weight for s in scores) / sum(s.weight for s in scores) if scores else 0
        analysis = await self._check_analysis_access(analysis_id)
        analysis.ux_score = round(total_score, 2)
        await self.db.commit()
        
        return scores
    
    async def get_scores_by_analysis(self, analysis_id: uuid.UUID) -> List[Score]:
        """Получает все сохранённые оценки анализа"""
        await self._check_analysis_access(analysis_id)
        result = await self.db.execute(
            select(Score).where(Score.analysis_id == analysis_id)
        )
        return result.scalars().all()