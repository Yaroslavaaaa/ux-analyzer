from sqlalchemy import String, Float, JSON, DateTime, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
from datetime import datetime

class MetricDefinition(Base):
    """Модель для связи с violations (только ID метрик)"""
    __tablename__ = "metric_definitions"
    
    # Только ID метрики - основное поле
    id: Mapped[str] = mapped_column(
        String(50), 
        primary_key=True,
        comment="ID метрики из metrics.json"
    )
    
    # Кэшируем основные данные для быстрых запросов
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # boolean, ratio, score
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    
    # Метаданные
    is_active: Mapped[bool] = mapped_column(default=True)
    version: Mapped[str] = mapped_column(String(20), default="1.0")
    
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
    # violations: Mapped[list["Violation"]] = relationship(
    #     back_populates="metric_definition",
    #     cascade="all, delete-orphan"
    # )
    # metric_values: Mapped[list["MetricValue"]] = relationship(
    #     back_populates="metric_definition"
    # )
    violations: Mapped[list["Violation"]] = relationship(
    back_populates="metric_definition",
    cascade="all, delete-orphan"
    )
    metric_values: Mapped[list["MetricValue"]] = relationship(
    back_populates="metric_definition",
    cascade="all, delete-orphan"
)
    
    # Индексы
    __table_args__ = (
        Index('ix_metric_definitions_category', 'category'),
    )

    @property
    def config(self) -> dict:
        """Получаем полную конфигурацию из JSON файла"""
        from app.core.metrics_loader import metrics_loader
        metric = metrics_loader.get_metric_by_id(self.id)
        return metric.get("config", {}) if metric else {}