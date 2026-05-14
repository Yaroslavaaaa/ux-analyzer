from sqlalchemy import JSON, String, ForeignKey, Float, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Score(Base):
    __tablename__ = "scores"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    category: Mapped[str] = mapped_column(
        String(100), 
        nullable=False,
        comment="Категория метрик (H1_Visibility, WCAG, ...)"
    )
    score: Mapped[float] = mapped_column(
        Float, 
        nullable=False,
        comment="Агрегированная оценка от 0 до 100"
    )
    
    # Опционально: вес категории в общем UX Score
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Детали расчёта (можно хранить JSON)
    details: Mapped[dict] = mapped_column(JSON, nullable=True)
    
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
    analysis: Mapped["Analysis"] = relationship(back_populates="scores")
    
    __table_args__ = (
        Index('ix_scores_analysis_category', 'analysis_id', 'category', unique=True),
    )