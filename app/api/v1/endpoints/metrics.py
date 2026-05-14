from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.core.database import get_db
from app.services.metric_service import MetricService
from app.core.metrics_loader import metrics_loader

router = APIRouter(prefix="/metrics", tags=["metrics"])

# Простая защита для разработчика (можно закомментировать в продакшене)
DEVELOPER_SECRET = "dev-secret-key-123"  # В реальности вынесите в .env

def verify_developer(secret: str = Query(..., description="Секретный ключ разработчика")):
    """Простая проверка доступа для разработчика"""
    if secret != DEVELOPER_SECRET:
        raise HTTPException(status_code=403, detail="Access denied. Developer only.")
    return True

@router.get("/all")
async def get_all_metrics(
    auth: bool = Depends(verify_developer),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEVELOPER ONLY] Получить все метрики из файла с полной конфигурацией
    """
    service = MetricService(db)
    metrics = service.get_all_metrics_from_file()
    categories = service.get_categories()
    
    return {
        "total": len(metrics),
        "categories": categories,
        "metrics": metrics
    }

@router.get("/categories")
async def get_categories(
    auth: bool = Depends(verify_developer),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEVELOPER ONLY] Получить все категории метрик
    """
    service = MetricService(db)
    categories = service.get_categories()
    
    return {
        "total": len(categories),
        "categories": categories
    }

@router.get("/category/{category}")
async def get_metrics_by_category(
    category: str,
    auth: bool = Depends(verify_developer),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEVELOPER ONLY] Получить метрики по категории
    """
    service = MetricService(db)
    metrics = service.get_metrics_by_category_from_file(category)
    
    if not metrics:
        raise HTTPException(status_code=404, detail=f"Category '{category}' not found")
    
    return {
        "category": category,
        "total": len(metrics),
        "metrics": metrics
    }

@router.get("/{metric_id}")
async def get_metric_by_id(
    metric_id: str,
    auth: bool = Depends(verify_developer),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEVELOPER ONLY] Получить метрику по ID с полной конфигурацией
    """
    service = MetricService(db)
    
    # Получаем из файла
    metric = service.get_metric_config(metric_id)
    
    if not metric:
        raise HTTPException(status_code=404, detail=f"Metric '{metric_id}' not found")
    
    # Получаем из БД (кэшированные данные)
    db_metric = await service.get_metric_definition(metric_id)
    
    return {
        "metric": metric,
        "db_info": {
            "id": db_metric.id,
            "name": db_metric.name,
            "category": db_metric.category,
            "type": db_metric.type,
            "weight": db_metric.weight,
            "is_active": db_metric.is_active,
            "created_at": db_metric.created_at,
            "updated_at": db_metric.updated_at
        } if db_metric else None
    }

@router.post("/reload")
async def reload_metrics(
    auth: bool = Depends(verify_developer),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEVELOPER ONLY] Перезагрузить метрики из файла и синхронизировать с БД
    """
    from app.scripts.sync_metrics import sync_metrics
    
    # Перезагружаем кэш
    metrics_loader.reload()
    
    # Синхронизируем с БД
    await sync_metrics()
    
    return {
        "message": "Metrics reloaded and synchronized successfully",
        "timestamp": str(metrics_loader._last_load) if metrics_loader._last_load else None
    }

@router.get("/sync/status")
async def get_sync_status(
    auth: bool = Depends(verify_developer),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEVELOPER ONLY] Получить статус синхронизации метрик
    """
    service = MetricService(db)
    
    # Метрики из файла
    file_metrics = service.get_all_metrics_from_file()
    file_ids = set(m["id"] for m in file_metrics)
    
    # Метрики из БД
    db_metrics = await service.get_all_metric_definitions()
    db_ids = set(m.id for m in db_metrics)
    
    # Находим расхождения
    only_in_file = file_ids - db_ids
    only_in_db = db_ids - file_ids
    
    return {
        "file_metrics_count": len(file_metrics),
        "db_metrics_count": len(db_metrics),
        "only_in_file": list(only_in_file),
        "only_in_db": list(only_in_db),
        "is_synced": len(only_in_file) == 0 and len(only_in_db) == 0,
        "last_sync": str(metrics_loader._last_load) if metrics_loader._last_load else "Never"
    }