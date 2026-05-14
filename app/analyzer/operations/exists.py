"""Операция exists: проверяет существование хотя бы одного элемента по условию."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation


class ExistsOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        selectors = config.get("selectors", [])
        text_contains = config.get("text_contains", [])

        matching = elements
        if selectors:
            matching = [el for el in matching if any(self._filter_by_selector([el], sel) for sel in selectors)]
        if text_contains:
            matching = self._filter_by_text_contains(matching, text_contains)

        value = 1.0 if matching else 0.0
        message = f"Найдены элементы по условию: {len(matching)}" if matching else "Элементы не найдены"
        return value, matching, message