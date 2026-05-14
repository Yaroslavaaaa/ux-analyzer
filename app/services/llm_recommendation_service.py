import aiohttp
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.violation import Violation
from app.models.element import Element
from app.models.metric_definition import MetricDefinition

logger = logging.getLogger(__name__)

class LLMRecommendationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def generate_recommendation(self, violation: Violation) -> Optional[str]:
        """Генерирует рекомендацию для одного нарушения."""
        # Получаем метрику (обязательно)
        metric = await self.db.get(MetricDefinition, violation.metric_id)
        if not metric:
            logger.warning(f"Metric {violation.metric_id} not found, skip recommendation")
            return None

        # Получаем элемент, если привязан
        element = None
        if violation.element_id:
            element = await self.db.get(Element, violation.element_id)

        # Формируем промпт
        prompt = self._build_prompt(violation, metric, element)

        # Вызываем OpenRouter API
        recommendation = await self._call_openrouter(prompt)
        return recommendation

    def _build_prompt(self, violation: Violation, metric: MetricDefinition, element: Optional[Element]) -> str:
        """Собирает промпт с контекстом нарушения."""
        base_prompt = (
            "Ты – эксперт по UX/UI, который даёт короткие, понятные рекомендации "
            "владельцам сайтов для улучшения юзабилити. Отвечай только на русском языке. "
            "Будь конкретен, указывай, что именно исправить и как. "
            "Не пиши 'следует', 'рекомендуется' – пиши повелительное наклонение: "
            "'Добавьте', 'Увеличьте', 'Измените'.\n\n"
        )

        context = f"Нарушение: {violation.message}\n"
        context += f"Метрика: {metric.name} (категория: {metric.category})\n"

        if element:
            context += f"Тип элемента: {element.element_type}\n"
            if element.text:
                context += f"Текст элемента: '{element.text}'\n"
            if element.has_alt is not None:
                context += f"alt-атрибут: {'есть' if element.has_alt else 'нет'}\n"
            if element.has_label is not None:
                context += f"aria-label: {'есть' if element.has_label else 'нет'}\n"

        context += "\nНапиши одну короткую рекомендацию (1-2 предложения):"
        return base_prompt + context

    async def _call_openrouter(self, prompt: str) -> Optional[str]:
        """Вызывает OpenRouter API и возвращает текст ответа."""
        headers = {
            "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        data = {
            "model": settings.OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 150,
            "temperature": 0.7,
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(
                    f"{settings.OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as resp:
                    if resp.status == 200:
                        result = await resp.json()
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        error_text = await resp.text()
                        logger.error(f"OpenRouter error {resp.status}: {error_text}")
                        return None
            except Exception as e:
                logger.error(f"OpenRouter request failed: {e}")
                return None