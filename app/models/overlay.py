from sqlalchemy import String, ForeignKey, Float, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class Severity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class Overlay(Base):
    __tablename__ = "overlays"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Опциональная связь с конкретным DOM-элементом (если подсветка привязана к элементу)
    element_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elements.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    # Координаты и размеры прямоугольника (поверх страницы)
    x: Mapped[float] = mapped_column(Float, nullable=False)
    y: Mapped[float] = mapped_column(Float, nullable=False)
    width: Mapped[float] = mapped_column(Float, nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=False)
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    
    # Опционально: цвет в формате HEX (если хотите кастомизировать)
    color: Mapped[str] = mapped_column(String(7), nullable=True)  # например, "#ff0000"
    
    # Текст подсказки, который показывается при наведении
    tooltip: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="overlays")
    element: Mapped["Element"] = relationship(back_populates="overlays")