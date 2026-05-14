from sqlalchemy import String, ForeignKey, Integer, Float, Boolean, Text, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Element(Base):
    __tablename__ = "elements"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    page_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("pages.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Основная информация об элементе
    element_type: Mapped[str] = mapped_column(String(50), nullable=False)  # button, img, input, a, div...
    text: Mapped[str] = mapped_column(Text, nullable=True)  # Текстовое содержимое
    
    # Позиция и размеры
    x: Mapped[float] = mapped_column(Float, nullable=True)
    y: Mapped[float] = mapped_column(Float, nullable=True)
    width: Mapped[float] = mapped_column(Float, nullable=True)
    height: Mapped[float] = mapped_column(Float, nullable=True)
    is_above_fold: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Визуальные характеристики
    font_size: Mapped[int] = mapped_column(Integer, nullable=True)  # px
    contrast_ratio: Mapped[float] = mapped_column(Float, nullable=True)  # от 1 до 21
    
    # Accessibility
    has_alt: Mapped[bool] = mapped_column(Boolean, default=False)
    has_label: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Временная метка
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    page: Mapped["Page"] = relationship(back_populates="elements")
    # violations: Mapped[list["Violation"]] = relationship(back_populates="element")  # позже
    violations: Mapped[list["Violation"]] = relationship(
    back_populates="element",
    cascade="all, delete-orphan"
    )
    overlays: Mapped[list["Overlay"]] = relationship(
    back_populates="element",
    cascade="all, delete-orphan"
)
    
    __table_args__ = (
        Index('ix_elements_page_type', 'page_id', 'element_type'),
    )