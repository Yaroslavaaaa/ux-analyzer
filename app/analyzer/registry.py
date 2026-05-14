"""Реестр операций для метрик."""

from typing import Dict, Type
from app.analyzer.operations.base import Operation
from app.analyzer.operations.exists import ExistsOperation
from app.analyzer.operations.ratio import RatioOperation
from app.analyzer.operations.text_analysis import TextAnalysisOperation
from app.analyzer.operations.consistency import ConsistencyOperation
from app.analyzer.operations.pattern_detection import PatternDetectionOperation
from app.analyzer.operations.responsive_check import ResponsiveCheckOperation
from app.analyzer.operations.noise_estimation import NoiseEstimationOperation
from app.analyzer.operations.spacing_analysis import SpacingAnalysisOperation
from app.analyzer.operations.focus_order import FocusOrderOperation

OPERATIONS: Dict[str, Type[Operation]] = {
    "exists": ExistsOperation,
    "ratio": RatioOperation,
    "text_analysis": TextAnalysisOperation,
    "consistency": ConsistencyOperation,
    "pattern_detection": PatternDetectionOperation,
    "responsive_check": ResponsiveCheckOperation,
    "noise_estimation": NoiseEstimationOperation,
    "spacing_analysis": SpacingAnalysisOperation,
    "focus_order_check": FocusOrderOperation,
}