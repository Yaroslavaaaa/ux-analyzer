"""Базовый класс для всех операций."""

from abc import ABC, abstractmethod
from typing import List, Dict, Tuple

from app.analyzer.helpers.selector_matcher import matches_selector, matches_text_contains


class Operation(ABC):
    """Базовый класс для всех операций."""

    @abstractmethod
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        """
        Выполняет операцию над списком элементов.

        Args:
            elements: Список элементов, собранных со страницы (из Redis).
            config: Конфигурация операции из метрики.
            context: Дополнительный контекст (например, analysis_id).

        Returns:
            value (float): 0..1 для boolean/ratio, 0..100 для score.
            violating_elements (List[Dict]): Элементы, вызвавшие нарушение.
            message (str): Пояснение для сообщения нарушения.
        """
        pass

    def _filter_by_selector(self, elements: List[Dict], selector: str) -> List[Dict]:
        """Фильтрует элементы по CSS-селектору."""
        return [el for el in elements if matches_selector(el, selector)]

    def _filter_by_text_contains(self, elements: List[Dict], texts: List[str]) -> List[Dict]:
        """Фильтрует элементы по наличию подстроки в тексте."""
        return [el for el in elements if matches_text_contains(el, texts)]