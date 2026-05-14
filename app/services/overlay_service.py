from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException, status
from typing import List
from app.models.project import Project
from app.models.user import User
from app.models.analysis import Analysis
from app.models.overlay import Overlay
from app.schemas.overlay import OverlayCreate
import uuid

class OverlayService:
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
    
    async def create_overlay(self, overlay_data: OverlayCreate) -> Overlay:
        """Создаёт подсветку (вызывается во время анализа)"""
        await self._check_analysis_access(overlay_data.analysis_id)
        
        overlay = Overlay(
            analysis_id=overlay_data.analysis_id,
            element_id=overlay_data.element_id,
            x=overlay_data.x,
            y=overlay_data.y,
            width=overlay_data.width,
            height=overlay_data.height,
            severity=overlay_data.severity,
            color=overlay_data.color,
            tooltip=overlay_data.tooltip
        )
        self.db.add(overlay)
        await self.db.commit()
        await self.db.refresh(overlay)
        return overlay
    
    async def get_overlays_by_analysis(self, analysis_id: uuid.UUID) -> List[Overlay]:
        """Все подсветки для анализа"""
        await self._check_analysis_access(analysis_id)
        result = await self.db.execute(
            select(Overlay).where(Overlay.analysis_id == analysis_id)
        )
        return result.scalars().all()
    
    async def delete_overlay(self, overlay_id: uuid.UUID) -> None:
        """Удалить подсветку"""
        result = await self.db.execute(
            select(Overlay).where(Overlay.id == overlay_id)
        )
        overlay = result.scalar_one_or_none()
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        await self._check_analysis_access(overlay.analysis_id)
        await self.db.delete(overlay)
        await self.db.commit()