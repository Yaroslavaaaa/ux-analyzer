"""Операция ratio: вычисляет долю элементов, удовлетворяющих условию."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation


class RatioOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        numerator_cfg = config.get("numerator")
        denominator_cfg = config.get("denominator")

        numerator_elements = self._apply_selector_condition(elements, numerator_cfg)
        denominator_elements = self._apply_selector_condition(elements, denominator_cfg)

        denominator_count = len(denominator_elements)
        if denominator_count == 0:
            value = 0.0
            violating_elements = []
            message = "Нет элементов в знаменателе"
        else:
            value = len(numerator_elements) / denominator_count
            # Нарушающие элементы = элементы знаменателя, которых нет в числителе
            violating_elements = [el for el in denominator_elements if el not in numerator_elements]
            message = f"{len(violating_elements)} из {denominator_count} элементов не удовлетворяют условию"

        return value, violating_elements, message

    def _apply_selector_condition(self, elements: List[Dict], cfg: Dict) -> List[Dict]:
        selector = cfg.get("selector")
        condition = cfg.get("condition")
        text_contains = cfg.get("text_contains", [])

        result = elements
        if selector:
            result = self._filter_by_selector(result, selector)

        if condition == "has_feedback":
            result = [el for el in result if el.get("has_feedback", False)]
        elif condition == "has_label":
            result = [el for el in result if el.get("has_label", False)]
        elif condition == "has_marker":
            result = [el for el in result if el.get("required_marker", False)]
        elif condition == "is_focusable":
            focusable_tags = {"button", "a", "input", "textarea", "select"}
            result = [el for el in result if el.get("tag") in focusable_tags]
        elif condition == "has_discernible_text":
            result = [el for el in result if el.get("text") and len(el["text"].strip()) > 0]

        if text_contains:
            result = self._filter_by_text_contains(result, text_contains)

        return result