from sqlalchemy import String, ForeignKey, Integer, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base
import uuid
from datetime import datetime

class Page(Base):
    __tablename__ = "pages"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    analysis_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("analyses.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    page_height: Mapped[int] = mapped_column(Integer, nullable=True)
    viewport_height: Mapped[int] = mapped_column(Integer, nullable=True)
    scroll_depth_ratio: Mapped[float] = mapped_column(Float, nullable=True)
    screenshot_url: Mapped[str] = mapped_column(String(500), nullable=True)
    overlay_screenshot_url: Mapped[str] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    analysis: Mapped["Analysis"] = relationship(back_populates="pages")  # добавим позже в Analysisы
    elements: Mapped[list["Element"]] = relationship(back_populates="page", cascade="all, delete-orphan")