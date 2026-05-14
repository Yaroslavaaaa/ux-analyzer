"""Операция text_analysis: NLP-анализ текста страницы."""

from typing import List, Dict, Tuple
from app.analyzer.operations.base import Operation
from app.analyzer.nlp.simplicity import analyze_text_simplicity


class TextAnalysisOperation(Operation):
    async def execute(self, elements: List[Dict], config: Dict, context: Dict) -> Tuple[float, List[Dict], str]:
        rule = config.get("rule", "simple_language_ratio")
        # Собираем весь текст со страницы (из атрибута 'text' элементов)
        texts = [el.get("text", "") for el in elements if el.get("text")]
        full_text = " ".join(texts)

        if rule == "simple_language_ratio":
            score = await analyze_text_simplicity(full_text)   # 0..100
            message = f"Оценка простоты языка: {score}"
        elif rule == "clarity":
            score = await analyze_text_simplicity(full_text)   # пока используем ту же метрику
            message = f"Оценка понятности текста: {score}"
        else:
            score = 100.0
            message = "Анализ текста не выполнен (неизвестное правило)"

        # Для text_analysis обычно нет конкретных нарушающих элементов, возвращаем пустой список
        return score, [], message