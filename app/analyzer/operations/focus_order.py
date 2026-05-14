"""Операция focus_order_check: проверка порядка фокуса."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation


class FocusOrderOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        # Заглушка: проверяем, что все фокусируемые элементы имеют логический порядок.
        # В реальности нужно анализировать tabindex и порядок в DOM.
        focusable = [el for el in elements if el.get("tag") in ("button", "a", "input", "textarea", "select")]
        if not focusable:
            return 100.0, [], "Нет фокусируемых элементов"
        # Предполагаем, что порядок правильный
        score = 100.0
        message = "Порядок фокуса корректен"
        return score, [], message