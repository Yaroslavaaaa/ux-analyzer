"""Вспомогательные функции для работы с текстом."""

def extract_text_from_elements(elements: list) -> str:
    """Извлекает весь текст из списка элементов."""
    texts = [el.get("text", "") for el in elements if el.get("text")]
    return " ".join(texts)