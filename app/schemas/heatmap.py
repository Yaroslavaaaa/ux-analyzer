from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Any, Dict
import uuid
from enum import Enum

class HeatmapTypeEnum(str, Enum):
    CLICK = "click"
    VIOLATION = "violation"
    SCROLL = "scroll"
    MOVEMENT = "movement"
    DENSITY = "density"

class Point(BaseModel):
    x: int
    y: int
    weight: float = 1.0  # интенсивность (например, несколько кликов в одной точке)

class HeatmapData(BaseModel):
    # Один из форматов:
    # 1. Список точек
    points: Optional[List[Point]] = None
    # 2. Матрица интенсивности (ширина x высота, значения 0..1 или количество)
    matrix: Optional[List[List[float]]] = None
    # 3. Сырые события (например, координаты кликов без агрегации)
    raw_events: Optional[List[Dict[str, Any]]] = None
    # Дополнительные метаданные
    bin_size: Optional[int] = 20  # размер ячейки для матрицы
    max_intensity: Optional[float] = None

class HeatmapBase(BaseModel):
    type: HeatmapTypeEnum
    data: Dict[str, Any]  # на самом деле валидируется как HeatmapData
    viewport_width: Optional[int] = None
    viewport_height: Optional[int] = None
    points_count: int = 0

class HeatmapCreate(HeatmapBase):
    analysis_id: uuid.UUID

class HeatmapUpdate(BaseModel):
    data: Optional[Dict[str, Any]] = None
    points_count: Optional[int] = None

class HeatmapResponse(HeatmapBase):
    id: uuid.UUID
    analysis_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True