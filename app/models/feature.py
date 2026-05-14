from sqlalchemy import String, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid

class Feature(Base):
    __tablename__ = "features"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analyses.id", ondelete="CASCADE"), nullable=False)
    key: Mapped[str] = mapped_column(String(255), nullable=False)
    value: Mapped[float] = mapped_column(Float, nullable=False)
    
    __table_args__ = (UniqueConstraint('analysis_id', 'key', name='uix_analysis_feature'),)
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="features")