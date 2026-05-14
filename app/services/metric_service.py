from typing import List, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.metric_definition import MetricDefinition
from app.core.metrics_loader import metrics_loader

class MetricService:
    """Сервис для работы с метриками (только для внутреннего использования)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_all_metric_definitions(self) -> List[MetricDefinition]:
        """Получает все метрики из БД"""
        result = await self.db.execute(select(MetricDefinition))
        return result.scalars().all()
    
    async def get_metric_definition(self, metric_id: str) -> Optional[MetricDefinition]:
        """Получает метрику по ID"""
        result = await self.db.execute(
            select(MetricDefinition).where(MetricDefinition.id == metric_id)
        )
        return result.scalar_one_or_none()
    
    def get_metric_config(self, metric_id: str) -> Optional[dict]:
        """Получает конфигурацию метрики из JSON файла"""
        return metrics_loader.get_metric_by_id(metric_id)
    
    async def validate_metric_id(self, metric_id: str) -> bool:
        """Проверяет существует ли метрика"""
        metric = await self.get_metric_definition(metric_id)
        return metric is not None
    
    def get_all_metrics_from_file(self) -> List[dict]:
        """Получает все метрики из файла (для разработчика)"""
        metrics, _ = metrics_loader.load_metrics()
        return metrics
    
    def get_categories(self) -> Dict[str, str]:
        """Получает все категории"""
        _, categories = metrics_loader.load_metrics()
        return categories
    
    def get_metrics_by_category_from_file(self, category: str) -> List[dict]:
        """Получает метрики по категории из файла"""
        return metrics_loader.get_metrics_by_category(category)
    
    def reload_metrics(self):
        """Перезагружает метрики из файла"""
        metrics_loader.reload()