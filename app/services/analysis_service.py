from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from fastapi import HTTPException, status
from typing import Optional, List
from app.models.user import User
from app.models.project import Project
from app.models.analysis import Analysis, AnalysisStatus
from app.schemas.analysis import AnalysisCreate, AnalysisUpdate
import uuid
from datetime import datetime

class AnalysisService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def _check_project_ownership(self, project_id: uuid.UUID) -> Project:
        """Проверяет, что проект принадлежит текущему пользователю"""
        result = await self.db.execute(
            select(Project).where(
                and_(
                    Project.id == project_id,
                    Project.user_id == self.current_user.id
                )
            )
        )
        project = result.scalar_one_or_none()
        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found or access denied"
            )
        return project
    
    async def create_analysis(self, project_id: uuid.UUID, analysis_data: AnalysisCreate) -> Analysis:
        """Создаёт новый анализ для проекта"""
        # Проверяем доступ к проекту
        project = await self._check_project_ownership(project_id)
        
        # Создаём анализ
        analysis = Analysis(
            project_id=project_id,
            url=analysis_data.url,
            status=AnalysisStatus.PENDING
        )
        self.db.add(analysis)
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis
    
    async def get_analysis_by_id(self, analysis_id: uuid.UUID) -> Analysis:
        """Получает анализ по ID с проверкой доступа через проект"""
        result = await self.db.execute(
            select(Analysis).where(Analysis.id == analysis_id)
        )
        analysis = result.scalar_one_or_none()
        if not analysis:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Analysis not found"
            )
        # Проверяем, что пользователь владеет проектом
        await self._check_project_ownership(analysis.project_id)
        return analysis
    
    async def get_project_analyses(
        self,
        project_id: uuid.UUID,
        skip: int = 0,
        limit: int = 100,
        status_filter: Optional[AnalysisStatus] = None
    ) -> tuple[List[Analysis], int]:
        """Получает список анализов проекта с пагинацией и фильтром по статусу"""
        # Проверяем доступ к проекту
        await self._check_project_ownership(project_id)
        
        # Базовый запрос
        query = select(Analysis).where(Analysis.project_id == project_id)
        
        if status_filter:
            query = query.where(Analysis.status == status_filter)
        
        # Подсчёт общего количества
        count_query = select(func.count()).select_from(query.subquery())
        total = await self.db.scalar(count_query)
        
        # Пагинация
        query = query.order_by(Analysis.created_at.desc()).offset(skip).limit(limit)
        result = await self.db.execute(query)
        analyses = result.scalars().all()
        
        return analyses, total or 0
    
    async def update_analysis(
        self,
        analysis_id: uuid.UUID,
        update_data: AnalysisUpdate
    ) -> Analysis:
        """Обновляет анализ (статус, UX score, временные метки)"""
        analysis = await self.get_analysis_by_id(analysis_id)
        
        update_dict = update_data.model_dump(exclude_unset=True)
        
        # Автоматически устанавливаем started_at при переходе в processing
        if update_dict.get("status") == AnalysisStatus.PROCESSING and analysis.status != AnalysisStatus.PROCESSING:
            update_dict["started_at"] = datetime.utcnow()
        
        # Автоматически устанавливаем completed_at при переходе в done или failed
        if update_dict.get("status") in (AnalysisStatus.DONE, AnalysisStatus.FAILED):
            update_dict["completed_at"] = datetime.utcnow()
        
        for field, value in update_dict.items():
            if hasattr(analysis, field) and value is not None:
                setattr(analysis, field, value)
        
        await self.db.commit()
        await self.db.refresh(analysis)
        return analysis
    
    async def delete_analysis(self, analysis_id: uuid.UUID) -> bool:
        """Удаляет анализ (hard delete)"""
        analysis = await self.get_analysis_by_id(analysis_id)
        await self.db.delete(analysis)
        await self.db.commit()
        return True
    
    async def get_analysis_stats(self, project_id: uuid.UUID) -> dict:
        """Получает статистику по анализам проекта"""
        await self._check_project_ownership(project_id)
        
        # Общее количество
        total_result = await self.db.execute(
            select(func.count()).where(Analysis.project_id == project_id)
        )
        total = total_result.scalar()
        
        # Количество по статусам
        status_counts = {}
        for status in AnalysisStatus:
            count_result = await self.db.execute(
                select(func.count()).where(
                    and_(
                        Analysis.project_id == project_id,
                        Analysis.status == status
                    )
                )
            )
            status_counts[status.value] = count_result.scalar() or 0
        
        # Средний UX score (только для завершённых)
        avg_score_result = await self.db.execute(
            select(func.avg(Analysis.ux_score)).where(
                and_(
                    Analysis.project_id == project_id,
                    Analysis.status == AnalysisStatus.DONE,
                    Analysis.ux_score.isnot(None)
                )
            )
        )
        avg_ux_score = avg_score_result.scalar()
        
        # Последний анализ
        last_result = await self.db.execute(
            select(Analysis)
            .where(Analysis.project_id == project_id)
            .order_by(Analysis.created_at.desc())
            .limit(1)
        )
        last_analysis = last_result.scalar_one_or_none()
        
        return {
            "total_analyses": total or 0,
            "status_counts": status_counts,
            "average_ux_score": float(avg_ux_score) if avg_ux_score else None,
            "last_analysis": {
                "id": str(last_analysis.id),
                "status": last_analysis.status.value,
                "ux_score": last_analysis.ux_score,
                "created_at": last_analysis.created_at
            } if last_analysis else None
        }