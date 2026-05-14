from PIL import Image, ImageDraw
from pathlib import Path
from typing import List
from app.models.overlay import Overlay


class OverlayRenderer:
    @staticmethod
    def severity_to_color(severity: str) -> str:
        """Цвет прямоугольника в зависимости от критичности."""
        mapping = {
            "critical": "#ff0000",   # красный
            "warning": "#ffa500",    # оранжевый
            "info": "#00bfff"        # голубой
        }
        return mapping.get(severity, "#ffa500")

    @staticmethod
    async def render_overlays(
        screenshot_path: str,
        overlays: List[Overlay],
        output_path: str
    ) -> None:
        """
        Рисует прямоугольники оверлеев на скриншоте.
        screenshot_path – путь к исходному скриншоту
        overlays – список оверлеев из БД
        output_path – куда сохранить результат
        """
        img = Image.open(screenshot_path)
        draw = ImageDraw.Draw(img)

        for ov in overlays:
            color = ov.color or OverlayRenderer.severity_to_color(ov.severity.value)
            # Координаты уже в пикселях относительно размера скриншота
            x1, y1 = ov.x, ov.y
            x2, y2 = ov.x + ov.width, ov.y + ov.height
            draw.rectangle([x1, y1, x2, y2], outline=color, width=3)

        img.save(output_path)