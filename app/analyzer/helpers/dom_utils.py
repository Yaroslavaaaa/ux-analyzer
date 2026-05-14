"""Утилиты для фильтрации DOM-элементов."""

from typing import List, Dict


def filter_by_tag(elements: List[Dict], tag: str) -> List[Dict]:
    """Возвращает элементы с заданным тегом."""
    return [el for el in elements if el.get("tag") == tag]