"""Фабрика для создания элементов, нарушений и оверлеев."""

import uuid
import asyncio
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.element import Element
from app.models.violation import Violation, Severity
from app.models.overlay import Overlay
from app.models.page import Page
from app.models.recommendation import Recommendation
from app.core.database import async_session_maker
from app.services.llm_recommendation_service import LLMRecommendationService


async def _get_page_id_by_analysis(db: AsyncSession, analysis_id: str) -> str:
    """Возвращает ID первой страницы, связанной с анализом."""
    result = await db.execute(select(Page.id).where(Page.analysis_id == analysis_id).limit(1))
    page_id = result.scalar_one_or_none()
    if not page_id:
        raise ValueError(f"No page found for analysis {analysis_id}")
    return page_id


async def _generate_recommendation_background(violation_id: uuid.UUID):
    """Фоновая задача: вызывает LLM и сохраняет рекомендацию."""
    async with async_session_maker() as db:
        try:
            result = await db.execute(select(Violation).where(Violation.id == violation_id))
            violation = result.scalar_one_or_none()
            if not violation:
                return

            service = LLMRecommendationService(db)
            rec_text = await service.generate_recommendation(violation)

            if rec_text:
                rec = Recommendation(violation_id=violation.id, text=rec_text)
                db.add(rec)
                await db.commit()
                print(f"✅ Recommendation generated for violation {violation.id}")
            else:
                print(f"❌ No recommendation for violation {violation.id}")
        except Exception as e:
            print(f"Error generating recommendation: {e}")


async def save_violation(
    db: AsyncSession,
    analysis_id: str,
    metric_id: str,
    element_data: Optional[dict],
    message: str
) -> uuid.UUID:
    """Создаёт запись элемента (если передан element_data), нарушение и оверлей. Возвращает ID нарушения."""
    element_id = None
    if element_data:
        page_id = await _get_page_id_by_analysis(db, analysis_id)

        element = Element(
            page_id=page_id,
            element_type=element_data.get("tag", ""),
            text=element_data.get("text", ""),
            x=element_data.get("x"),
            y=element_data.get("y"),
            width=element_data.get("width"),
            height=element_data.get("height"),
            is_above_fold=element_data.get("is_above_fold", False),
            has_alt=element_data.get("has_alt", False),
            has_label=element_data.get("has_label", False),
            font_size=element_data.get("font_size"),
            contrast_ratio=element_data.get("contrast_ratio")
        )
        db.add(element)
        await db.flush()
        element_id = element.id

        overlay = Overlay(
            analysis_id=analysis_id,
            element_id=element_id,
            x=element_data.get("x", 0),
            y=element_data.get("y", 0),
            width=element_data.get("width", 0),
            height=element_data.get("height", 0),
            severity=Severity.WARNING,
            tooltip=message[:500]
        )
        db.add(overlay)

    violation = Violation(
        analysis_id=analysis_id,
        metric_id=metric_id,
        element_id=element_id,
        severity=Severity.WARNING,
        message=message
    )
    db.add(violation)
    await db.commit()
    await db.refresh(violation)

    # Запускаем фоновую генерацию рекомендации (не ждём результата)
    asyncio.create_task(_generate_recommendation_background(violation.id))

    return violation.id