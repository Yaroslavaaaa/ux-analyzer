"""Агрегация оценок по категориям."""

import logging
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.metric_value import MetricValue
from app.models.metric_definition import MetricDefinition
from app.models.score import Score
from app.models.analysis import Analysis

logger = logging.getLogger(__name__)

async def compute_and_save_scores(db: AsyncSession, analysis_id: str) -> None:
    stmt = (
        select(
            MetricDefinition.category,
            MetricDefinition.weight,
            MetricDefinition.type,
            MetricValue.value
        )
        .join(MetricValue, MetricDefinition.id == MetricValue.metric_id)
        .where(MetricValue.analysis_id == analysis_id)
    )
    rows = await db.execute(stmt)
    metrics_data = rows.all()

    if not metrics_data:
        return

    # Логируем сырые данные
    logger.info(f"Metrics data for analysis {analysis_id}:")
    for category, weight, mtype, value in metrics_data:
        logger.info(f"  cat={category}, weight={weight}, type={mtype}, value={value}")

    category_scores = {}
    category_weights = {}
    for category, weight, mtype, value in metrics_data:
        # Нормализация с жёсткой проверкой
        if mtype in ("boolean", "ratio"):
            # Ожидаем value в [0,1]
            normalized = value * 100.0
        elif mtype == "score":
            # Ожидаем value уже в [0,100]
            normalized = value
        else:
            # fallback
            normalized = value * 100.0 if value <= 1 else value

        # Ограничим sanity check
        if normalized > 100:
            logger.warning(f"Normalized value too high: {normalized} for metric type {mtype}, value={value}")
            normalized = min(normalized, 100.0)

        weighted_value = normalized * weight
        category_scores[category] = category_scores.get(category, 0.0) + weighted_value
        category_weights[category] = category_weights.get(category, 0.0) + weight

    await db.execute(Score.__table__.delete().where(Score.analysis_id == analysis_id))

    total_weighted = 0.0
    total_weight = 0.0

    for category, total_val in category_scores.items():
        cat_weight = category_weights[category]
        if cat_weight == 0:
            cat_score = 0.0
        else:
            cat_score = total_val / cat_weight
        total_weighted += cat_score * cat_weight
        total_weight += cat_weight

        score_obj = Score(
            analysis_id=analysis_id,
            category=category,
            score=cat_score,
            weight=cat_weight
        )
        db.add(score_obj)

    ux_score = total_weighted / total_weight if total_weight > 0 else 0.0
    await db.execute(
        update(Analysis)
        .where(Analysis.id == analysis_id)
        .values(ux_score=ux_score)
    )
    await db.commit()