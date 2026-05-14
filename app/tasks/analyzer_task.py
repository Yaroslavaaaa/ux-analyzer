async def analyze_page(analysis_id: str):
    """
    Заглушка: позже здесь будет разбор метрик, создание violations, элементов и т.д.
    """
    print(f"Analyzer started for analysis {analysis_id}")
    # В реальности:
    # - прочитать из Redis элементы
    # - применить метрики
    # - сохранить Element (только нарушающие)
    # - создать Violation, Score, Overlay, Recommendation
    # - обновить статус анализа на DONE
    # - очистить Redis кэш