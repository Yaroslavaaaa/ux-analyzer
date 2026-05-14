from sqlalchemy import String, ForeignKey, Float, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    DONE = "done"
    FAILED = "failed"

class Analysis(Base):
    __tablename__ = "analyses"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    project_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Основные данные
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    status: Mapped[AnalysisStatus] = mapped_column(
        Enum(AnalysisStatus),
        default=AnalysisStatus.PENDING,
        nullable=False
    )
    ux_score: Mapped[float] = mapped_column(Float, nullable=True)
    
    # Временные метки
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
    completed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )
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
    project: Mapped["Project"] = relationship(back_populates="analyses")
    # Позже добавим связи с pages, features, metric_values и т.д.
    # в классе Analysis добавьте:
    pages: Mapped[list["Page"]] = relationship(back_populates="analysis", cascade="all, delete-orphan")
    violations: Mapped[list["Violation"]] = relationship(
    back_populates="analysis", 
    cascade="all, delete-orphan"
    )
    scores: Mapped[list["Score"]] = relationship(
    back_populates="analysis", 
    cascade="all, delete-orphan"
    )
    overlays: Mapped[list["Overlay"]] = relationship(
    back_populates="analysis", 
    cascade="all, delete-orphan"
    )
    heatmaps: Mapped[list["Heatmap"]] = relationship(
    back_populates="analysis",
    cascade="all, delete-orphan"
    )
    metric_values: Mapped[list["MetricValue"]] = relationship(
    back_populates="analysis",
    cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Analysis {self.id} ({self.status.value})>"