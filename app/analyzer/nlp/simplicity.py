"""Функции для оценки простоты языка."""

async def analyze_text_simplicity(text: str) -> float:
    """
    Возвращает оценку простоты языка от 0 до 100.
    Чем проще язык, тем выше оценка.
    """
    if not text:
        return 100.0

    # Простейшая эвристика: средняя длина слов.
    words = text.split()
    if not words:
        return 100.0

    avg_word_len = sum(len(w) for w in words) / len(words)
    # Чем длиннее слова, тем сложнее язык.
    score = max(0, 100 - (avg_word_len - 4) * 10)
    # Ограничиваем порогом
    return min(100, score)