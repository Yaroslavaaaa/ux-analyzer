from sqlalchemy import String, ForeignKey, Float, DateTime, func, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime

class MetricValue(Base):
    __tablename__ = "metric_values"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    metric_id: Mapped[str] = mapped_column(
        ForeignKey("metric_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # Значение метрики:
    # - для boolean: 0.0 или 1.0
    # - для ratio: 0.0 .. 1.0
    # - для score: 0.0 .. 100.0
    value: Mapped[float] = mapped_column(Float, nullable=False)
    
    # Необязательные дополнительные данные (например, numerator, denominator)
    # Можно хранить breakdown вычисления для отладки
    raw_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="metric_values")
    metric_definition: Mapped["MetricDefinition"] = relationship(back_populates="metric_values")
    
    __table_args__ = (
        Index('ix_metric_values_analysis_metric', 'analysis_id', 'metric_id', unique=True),
    )