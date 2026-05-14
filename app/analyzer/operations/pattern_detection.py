"""Операция pattern_detection: поиск шаблонов (например, autofill, accesskey)."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation


class PatternDetectionOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        pattern = config.get("pattern")
        violating = []

        if pattern == "autofill":
            # Ищем элементы с атрибутом autocomplete
            violating = [el for el in elements if el.get("autocomplete") is not None]
            value = len(violating) / max(len(elements), 1)
            message = f"Найдено {len(violating)} элементов с автозаполнением"
        elif pattern == "accesskey":
            violating = [el for el in elements if el.get("accesskey") is not None]
            value = 1.0 if violating else 0.0
            message = "Есть клавиши доступа" if violating else "Нет клавиш доступа"
        else:
            value = 0.0
            message = "Неизвестный шаблон"

        # Возвращаем score (0..100)
        score = value * 100
        return score, violating, message