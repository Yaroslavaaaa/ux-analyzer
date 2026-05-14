from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.heatmap_service import HeatmapService
from app.schemas.heatmap import HeatmapResponse, HeatmapCreate
import uuid

router = APIRouter(prefix="/heatmaps", tags=["heatmaps"])

@router.get("/analysis/{analysis_id}/{type}", response_model=HeatmapResponse)
async def get_heatmap(
    analysis_id: uuid.UUID,
    type: str,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = HeatmapService(db, current_user)
    heatmap = await service.get_heatmap(analysis_id, type)
    return heatmap

@router.post("", response_model=HeatmapResponse)
async def create_or_update_heatmap(
    heatmap_data: HeatmapCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    service = HeatmapService(db, current_user)
    heatmap = await service.create_or_update_heatmap(heatmap_data)
    return heatmap