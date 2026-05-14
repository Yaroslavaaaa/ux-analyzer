from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.models.user import User
from app.services.overlay_service import OverlayService
from app.services.analysis_service import AnalysisService
from app.schemas.overlay import OverlayResponse
import uuid
from fastapi.responses import FileResponse
from pathlib import Path
from app.core.config import settings
from app.services.overlay_renderer import OverlayRenderer
from sqlalchemy import select
from app.models.page import Page

router = APIRouter(prefix="/overlays", tags=["overlays"])

# @router.get("/analysis/{analysis_id}", response_model=List[OverlayResponse])
# async def get_analysis_overlays(
#     analysis_id: uuid.UUID,
#     current_user: User = Depends(get_current_active_user),
#     db: AsyncSession = Depends(get_db)
# ):
#     """Все визуализации (подсветки) для анализа."""
#     service = OverlayService(db, current_user)
#     overlays = await service.get_overlays_by_analysis(analysis_id)
#     return overlays


@router.get("/analysis/{analysis_id}", response_model=List[OverlayResponse])
async def get_analysis_overlays(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Все визуализации (подсветки) для анализа."""
    service = OverlayService(db, current_user)
    overlays = await service.get_overlays_by_analysis(analysis_id)
    return overlays


@router.get("/analysis/{analysis_id}/visualization")
async def get_analysis_visualization(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает данные для отрисовки оверлеев на скриншоте:
    - screenshot_url: URL скриншота страницы
    - overlays: массив прямоугольников с координатами, цветом и подсказкой
    """
    # Проверяем доступ к анализу (через сервис)
    analysis_service = AnalysisService(db, current_user)
    analysis = await analysis_service.get_analysis_by_id(analysis_id)

    # Получаем страницу, связанную с анализом (первую)
    from app.models.page import Page
    from sqlalchemy import select
    result = await db.execute(select(Page).where(Page.analysis_id == analysis_id).limit(1))
    page = result.scalar_one_or_none()
    if not page or not page.screenshot_url:
        raise HTTPException(status_code=404, detail="Screenshot not found for this analysis")

    # Получаем оверлеи
    overlay_service = OverlayService(db, current_user)
    overlays = await overlay_service.get_overlays_by_analysis(analysis_id)

    # Преобразуем в формат для фронтенда
    def severity_color(severity: str) -> str:
        if severity == "critical":
            return "#ff0000"   # красный
        elif severity == "warning":
            return "#ffa500"   # оранжевый
        else:
            return "#00bfff"   # голубой

    overlays_data = [
        {
            "id": str(ov.id),
            "x": ov.x,
            "y": ov.y,
            "width": ov.width,
            "height": ov.height,
            "color": ov.color or severity_color(ov.severity.value),
            "tooltip": ov.tooltip or "",
            "severity": ov.severity.value
        }
        for ov in overlays
    ]

    return {
        "analysis_id": str(analysis_id),
        "screenshot_url": page.screenshot_url,
        "viewport_width": page.viewport_height,  # осторожно: ширина вьюпорта у нас не сохранена
        "viewport_height": page.viewport_height,
        "overlays": overlays_data
    }




@router.get("/analysis/{analysis_id}/overlay-image")
async def get_overlay_image(
    analysis_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Возвращает скриншот с нарисованными оверлеями (прямоугольниками нарушений).
    При первом запросе генерирует и сохраняет файл, при повторных отдаёт сохранённый.
    """
    # Проверяем доступ к анализу
    analysis_service = AnalysisService(db, current_user)
    analysis = await analysis_service.get_analysis_by_id(analysis_id)

    # Получаем страницу анализа
    result = await db.execute(select(Page).where(Page.analysis_id == analysis_id).limit(1))
    page = result.scalar_one_or_none()
    if not page or not page.screenshot_url:
        raise HTTPException(status_code=404, detail="Screenshot not found")

    # Если уже генерировали – отдаём готовый файл
    if page.overlay_screenshot_url:
        return FileResponse(
            path=page.overlay_screenshot_url.lstrip("/static/"),
            media_type="image/png",
            filename=f"{analysis_id}_overlay.png"
        )

    # Получаем оверлеи
    overlay_service = OverlayService(db, current_user)
    overlays = await overlay_service.get_overlays_by_analysis(analysis_id)

    if not overlays:
        # Нет нарушений – возвращаем чистый скриншот
        return FileResponse(
            path=page.screenshot_url.lstrip("/static/"),
            media_type="image/png",
            filename=f"{analysis_id}_original.png"
        )

    # Генерируем новый файл с оверлеями
    original_path = Path(settings.SCREENSHOTS_DIR) / Path(page.screenshot_url).name
    output_filename = f"{analysis_id}_overlay.png"
    output_path = Path(settings.SCREENSHOTS_DIR) / output_filename

    # Рисуем прямоугольники
    await OverlayRenderer.render_overlays(str(original_path), overlays, str(output_path))

    # Сохраняем URL в БД
    page.overlay_screenshot_url = f"/static/screenshots/{output_filename}"
    await db.commit()

    return FileResponse(output_path, media_type="image/png", filename=output_filename)