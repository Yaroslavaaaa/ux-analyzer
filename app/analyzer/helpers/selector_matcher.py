"""Простейший матчер CSS-селекторов на основе данных из элемента."""

import re
from typing import Dict, List


def matches_selector(element: Dict, selector: str) -> bool:
    """
    Проверяет, соответствует ли элемент CSS-селектору (упрощённая версия).

    Поддерживает:
        - тег (button, div)
        - класс (.classname)
        - id (#id)
        - атрибут ([attr], [attr=value])
    """
    selector = selector.strip()
    if not selector:
        return True

    # Селектор класса
    if selector.startswith("."):
        class_name = selector[1:]
        classes = element.get("class", "").split()
        return class_name in classes

    # Селектор ID
    if selector.startswith("#"):
        return element.get("id") == selector[1:]

    # Селектор атрибута
    if selector.startswith("["):
        match = re.match(r'\[(\w+)(?:=("|\')(.*?)\2)?\]', selector)
        if match:
            attr_name = match.group(1)
            attr_value = match.group(3) if match.group(3) else None
            existing = element.get(attr_name)
            if attr_value is not None:
                return existing == attr_value
            else:
                return existing is not None
        return False

    # Селектор тега
    return element.get("tag") == selector


def matches_text_contains(element: Dict, texts: List[str]) -> bool:
    """Проверяет, содержит ли текст элемента хотя бы одну из подстрок (без учёта регистра)."""
    el_text = element.get("text", "").lower()
    return any(t.lower() in el_text for t in texts)