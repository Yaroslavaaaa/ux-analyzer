import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class MetricsLoader:
    """Загрузчик метрик из JSON файла"""
    
    def __init__(self):
        self._metrics_cache: Optional[List[dict]] = None
        self._metrics_by_id: Optional[Dict[str, dict]] = None
        self._categories: Optional[Dict[str, str]] = None
        self._last_load: Optional[datetime] = None
        
    def _get_metrics_file_path(self) -> Path:
        """Получает путь к файлу с метриками"""
        # Ищем файл в разных местах
        possible_paths = [
            Path(__file__).parent.parent / "data" / "metrics.json",
            Path.cwd() / "app" / "data" / "metrics.json",
            Path.cwd() / "data" / "metrics.json",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        
        raise FileNotFoundError("metrics.json not found")
    
    def load_metrics(self, force_reload: bool = False) -> tuple[List[dict], Dict[str, str]]:
        """Загружает метрики из файла
        
        Returns:
            tuple: (список метрик, словарь категорий)
        """
        if not force_reload and self._metrics_cache is not None:
            return self._metrics_cache, self._categories
        
        try:
            file_path = self._get_metrics_file_path()
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self._metrics_cache = data.get("metrics", [])
            self._categories = data.get("categories", {})
            self._metrics_by_id = {
                m["id"]: m for m in self._metrics_cache
            }
            self._last_load = datetime.now()
            
            print(f"✅ Loaded {len(self._metrics_cache)} metrics from {file_path}")
            return self._metrics_cache, self._categories
            
        except Exception as e:
            print(f"❌ Error loading metrics: {e}")
            raise
    
    def get_metric_by_id(self, metric_id: str) -> Optional[dict]:
        """Получает метрику по ID"""
        if self._metrics_by_id is None:
            self.load_metrics()
        return self._metrics_by_id.get(metric_id)
    
    def get_metrics_by_category(self, category: str) -> List[dict]:
        """Получает метрики по категории"""
        metrics, _ = self.load_metrics()
        return [m for m in metrics if m.get("category") == category]
    
    def get_categories(self) -> Dict[str, str]:
        """Получает все категории с описаниями"""
        _, categories = self.load_metrics()
        return categories
    
    def reload(self):
        """Принудительная перезагрузка метрик"""
        self.load_metrics(force_reload=True)
    
    def validate_metric(self, metric: dict) -> bool:
        """Валидация структуры метрики"""
        required_fields = ["id", "category", "type", "config"]
        return all(field in metric for field in required_fields)

# Создаем глобальный экземпляр
metrics_loader = MetricsLoader()