from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from fastapi import HTTPException
from typing import List
from app.models.user import User
from app.models.analysis import Analysis
from app.models.heatmap import Heatmap
from app.schemas.heatmap import HeatmapCreate
import uuid

class HeatmapService:
    def __init__(self, db: AsyncSession, current_user: User):
        self.db = db
        self.current_user = current_user
    
    async def _check_analysis_access(self, analysis_id: uuid.UUID):
        # аналогично другим сервисам
        ...
    
    async def create_or_update_heatmap(self, heatmap_data: HeatmapCreate) -> Heatmap:
        await self._check_analysis_access(heatmap_data.analysis_id)
        # проверяем, существует ли уже тепловая карта такого типа для этого анализа
        existing = await self.db.execute(
            select(Heatmap).where(
                and_(
                    Heatmap.analysis_id == heatmap_data.analysis_id,
                    Heatmap.type == heatmap_data.type
                )
            )
        )
        heatmap = existing.scalar_one_or_none()
        if heatmap:
            # обновляем
            heatmap.data = heatmap_data.data
            heatmap.points_count = heatmap_data.points_count
            heatmap.viewport_width = heatmap_data.viewport_width
            heatmap.viewport_height = heatmap_data.viewport_height
        else:
            heatmap = Heatmap(**heatmap_data.model_dump())
            self.db.add(heatmap)
        await self.db.commit()
        await self.db.refresh(heatmap)
        return heatmap
    
    async def get_heatmap(self, analysis_id: uuid.UUID, type: str) -> Heatmap:
        await self._check_analysis_access(analysis_id)
        result = await self.db.execute(
            select(Heatmap).where(
                and_(
                    Heatmap.analysis_id == analysis_id,
                    Heatmap.type == type
                )
            )
        )
        heatmap = result.scalar_one_or_none()
        if not heatmap:
            raise HTTPException(status_code=404, detail="Heatmap not found")
        return heatmap