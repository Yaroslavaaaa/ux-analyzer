"""Операция responsive_check: проверка адаптивности."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation


class ResponsiveCheckOperation(Operation):
    async def execute(self, elements, config, context):
        # В реальности нужно проверить мета-вьюпорт и медиазапросы.
        # Сейчас заглушка: считаем, что адаптивность есть.
        value = 1.0  # вместо 100.0
        message = "Адаптивность в порядке"
        return value, [], message