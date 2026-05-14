from sqlalchemy import String, ForeignKey, Text, DateTime, func, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime
import enum

class Severity(str, enum.Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"

class Violation(Base):
    __tablename__ = "violations"
    
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
    # Ссылка на конкретный DOM-элемент (если нарушение привязано к элементу)
    element_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("elements.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    severity: Mapped[Severity] = mapped_column(Enum(Severity), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now()
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="violations")
    metric_definition: Mapped["MetricDefinition"] = relationship(back_populates="violations")
    element: Mapped["Element"] = relationship(back_populates="violations")
    recommendations: Mapped[list["Recommendation"]] = relationship(
    back_populates="violation",
    cascade="all, delete-orphan"
)