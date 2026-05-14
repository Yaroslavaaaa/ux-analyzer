"""Операция consistency: проверяет консистентность атрибутов у группы элементов."""

from typing import List, Dict, Tuple
from collections import Counter
from app.analyzer.operations.base import Operation


class ConsistencyOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        target = config.get("target")          # "button", "a", "components"
        attribute = config.get("attribute")    # "class", ["href", "target"]

        # Фильтруем элементы по типу
        if target == "components":
            filtered = elements
        else:
            filtered = [el for el in elements if el.get("tag") == target]

        if not filtered:
            return 1.0, [], "Нет элементов для проверки консистентности"

        # Собираем значения атрибутов
        if isinstance(attribute, list):
            values = [tuple(el.get(attr, "") for attr in attribute) for el in filtered]
        else:
            values = [el.get(attribute, "") for el in filtered]

        counter = Counter(values)
        most_common_count = counter.most_common(1)[0][1]
        consistency_ratio = most_common_count / len(filtered)   # 0..1
        # Преобразуем в score 0..100, штрафуем если < 0.7
        if consistency_ratio >= 0.7:
            score = consistency_ratio * 100
        else:
            score = consistency_ratio * 100 * 0.5

        message = f"Консистентность {target} по атрибуту {attribute}: {int(consistency_ratio*100)}%"
        # Элементы, которые не соответствуют самому популярному значению
        most_common_value = counter.most_common(1)[0][0]
        violating = [el for el, val in zip(filtered, values) if val != most_common_value]

        return score, violating, message