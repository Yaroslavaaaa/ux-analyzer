import enum

from sqlalchemy import Enum, Integer, String, ForeignKey, JSON, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime

class HeatmapType(str, enum.Enum):
    CLICK = "click"
    VIOLATION = "violation"
    SCROLL = "scroll"
    MOVEMENT = "movement"  # движение мыши
    DENSITY = "density"    # общая плотность элементов

class Heatmap(Base):
    __tablename__ = "heatmaps"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[HeatmapType] = mapped_column(
        Enum(HeatmapType),
        nullable=False
    )
    # Основные данные – JSONB с точками и/или матрицей интенсивности
    data: Mapped[dict] = mapped_column(JSON, nullable=False)
    # Опционально: метаданные (разрешение, область действия)
    viewport_width: Mapped[int] = mapped_column(Integer, nullable=True)
    viewport_height: Mapped[int] = mapped_column(Integer, nullable=True)
    # Количество точек/событий, участвовавших в построении (для статистики)
    points_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="heatmaps")
    
    __table_args__ = (
        Index('ix_heatmaps_analysis_type', 'analysis_id', 'type', unique=True),
    )