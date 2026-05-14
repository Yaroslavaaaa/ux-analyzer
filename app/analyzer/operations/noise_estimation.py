"""Операция noise_estimation: оценка визуального шума."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation


class NoiseEstimationOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        # Заглушка: вычисляем "шум" как плотность элементов (чем больше элементов, тем хуже)
        density = len(elements) / 1000   # примерный коэффициент
        noise_score = max(0, 100 - density * 10)
        message = f"Оценка визуального шума: {noise_score:.1f}"
        return noise_score, [], message