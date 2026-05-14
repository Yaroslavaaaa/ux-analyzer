"""Главный движок анализа."""

import json
from datetime import datetime
from typing import List
import uuid
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.redis_client import RedisClient
from app.core.metrics_loader import metrics_loader
from app.analyzer.registry import OPERATIONS
from app.analyzer.violation_factory import save_violation
from app.analyzer.aggregator import compute_and_save_scores
from app.models.metric_value import MetricValue
from app.models.analysis import Analysis, AnalysisStatus


async def run_analysis(analysis_id: str, db: AsyncSession) -> List[uuid.UUID]:
    """
    Запускает полный цикл анализа для заданного analysis_id.
    Возвращает список ID созданных нарушений.
    """
    # 1. Получаем элементы из Redis
    redis = await RedisClient.get_client()
    cache_key = f"analysis:{analysis_id}:elements"
    elements_json = await redis.get(cache_key)
    if not elements_json:
        await _update_analysis_status(db, analysis_id, AnalysisStatus.FAILED)
        return []

    elements = json.loads(elements_json)
    metrics, _ = metrics_loader.load_metrics()

    violation_ids = []

    for metric in metrics:
        metric_id = metric["id"]
        metric_type = metric["type"]
        config = metric.get("config", {})
        op_name = config.get("operation")
        if op_name not in OPERATIONS:
            continue

        operation = OPERATIONS[op_name]()
        value, violating_elements, message = await operation.execute(elements, config, {"analysis_id": analysis_id})

        metric_value = MetricValue(
            analysis_id=analysis_id,
            metric_id=metric_id,
            value=value,
            raw_data={"violating_count": len(violating_elements)}
        )
        db.add(metric_value)
        await db.flush()

        threshold = metric.get("threshold", 0.8)
        is_violation = False
        if metric_type == "boolean":
            is_violation = (value == 0)
        elif metric_type in ("ratio", "score"):
            is_violation = (value < threshold)

        if is_violation:
            if violating_elements:
                for el_data in violating_elements:
                    v_id = await save_violation(db, analysis_id, metric_id, el_data, message)
                    violation_ids.append(v_id)
            else:
                v_id = await save_violation(db, analysis_id, metric_id, None, message)
                violation_ids.append(v_id)

    await compute_and_save_scores(db, analysis_id)
    await _update_analysis_status(db, analysis_id, AnalysisStatus.DONE, completed_at=datetime.utcnow())

    return violation_ids


async def _update_analysis_status(db: AsyncSession, analysis_id: str, status: AnalysisStatus, completed_at=None):
    stmt = (
        update(Analysis)
        .where(Analysis.id == analysis_id)
        .values(status=status, completed_at=completed_at)
    )
    await db.execute(stmt)
    await db.commit()