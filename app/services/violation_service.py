from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List, Optional
from app.models.user import User
from app.models.analysis import Analysis
from app.models.violation import Violation
from app.models.project import Project
from app.schemas.violation import ViolationCreate
import uuid

class ViolationService:
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
    
    async def create_violation(self, violation_data: ViolationCreate) -> Violation:
        """Создаёт нарушение (вызывается во время анализа)"""
        await self._check_analysis_access(violation_data.analysis_id)
        
        violation = Violation(
            analysis_id=violation_data.analysis_id,
            metric_id=violation_data.metric_id,
            element_id=violation_data.element_id,
            severity=violation_data.severity,
            message=violation_data.message
        )
        self.db.add(violation)
        await self.db.commit()
        await self.db.refresh(violation)
        return violation
    
    async def get_violations_by_analysis(self, analysis_id: uuid.UUID) -> List[Violation]:
        """Получает все нарушения для анализа"""
        await self._check_analysis_access(analysis_id)
        result = await self.db.execute(
            select(Violation).where(Violation.analysis_id == analysis_id)
        )
        return result.scalars().all()
    
    async def get_violation(self, violation_id: uuid.UUID) -> Violation:
        """Получает нарушение по ID с проверкой прав"""
        result = await self.db.execute(
            select(Violation).where(Violation.id == violation_id)
        )
        violation = result.scalar_one_or_none()
        if not violation:
            raise HTTPException(status_code=404, detail="Violation not found")
        await self._check_analysis_access(violation.analysis_id)
        return violation
    
    async def delete_violation(self, violation_id: uuid.UUID) -> None:
        """Удаляет нарушение"""
        violation = await self.get_violation(violation_id)
        await self.db.delete(violation)
        await self.db.commit()