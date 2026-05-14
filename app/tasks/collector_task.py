import asyncio
import sys
from playwright.sync_api import sync_playwright
from sqlalchemy import func, update
from app.core.database import async_session_maker
from app.core.redis_client import RedisClient
from app.core.config import settings
from app.models.analysis import Analysis, AnalysisStatus
from app.models.page import Page
import json
from pathlib import Path

def _collect_sync(analysis_id: str, page_id: str, url: str):
    """Синхронная часть сбора данных (запускается в отдельном потоке)."""
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=['--disable-blink-features=AutomationControlled']
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        )
        page = context.new_page()

        # Используем более мягкое ожидание
        page.goto(url, timeout=settings.COLLECTOR_TIMEOUT * 1000, wait_until="domcontentloaded")
        # Ждём, пока тело страницы не загрузится (можно и load)
        page.wait_for_load_state("load")
        # Дополнительная пауза для динамического контента (опционально)
        page.wait_for_timeout(2000)

        viewport_height = page.evaluate("window.innerHeight")
        total_height = page.evaluate("document.body.scrollHeight")
        screenshot_bytes = page.screenshot(full_page=True)

        # Сохраняем скриншот
        screenshots_dir = Path(settings.SCREENSHOTS_DIR)
        screenshots_dir.mkdir(parents=True, exist_ok=True)
        screenshot_filename = f"{analysis_id}_{page_id}.png"
        screenshot_path = screenshots_dir / screenshot_filename
        with open(screenshot_path, "wb") as f:
            f.write(screenshot_bytes)
        screenshot_url = f"/static/screenshots/{screenshot_filename}"

        # Собираем интерактивные элементы (без изменений)
        elements_data = page.evaluate('''
            () => {
                const interactiveSelectors = [
                    'button', 'a', 'input', 'textarea', 'select',
                    'img', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
                    '[role="button"]', '[contenteditable="true"]'
                ];
                const elements = document.querySelectorAll(interactiveSelectors.join(','));
                const viewportHeight = window.innerHeight;
                const results = [];

                for (const el of elements) {
                    const rect = el.getBoundingClientRect();
                    const isAboveFold = rect.y < viewportHeight;
                    const computedStyle = window.getComputedStyle(el);
                    const fontSize = parseInt(computedStyle.fontSize);
                    const contrastRatio = null;

                    results.push({
                        tag: el.tagName.toLowerCase(),
                        type: el.getAttribute('type') || '',
                        text: (el.innerText || el.value || '').trim().substring(0, 500),
                        x: Math.round(rect.x),
                        y: Math.round(rect.y),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height),
                        is_above_fold: isAboveFold,
                        has_alt: !!el.getAttribute('alt'),
                        has_label: !!(el.getAttribute('aria-label') || el.getAttribute('aria-labelledby')),
                        font_size: fontSize,
                        contrast_ratio: contrastRatio
                    });
                }
                return results;
            }
        ''')
        browser.close()
        return total_height, viewport_height, screenshot_url, elements_data

async def collect_page_data(analysis_id: str, page_id: str, url: str):
    # Обновляем статус анализа на PROCESSING
    async with async_session_maker() as db:
        stmt = update(Analysis).where(Analysis.id == analysis_id).values(status=AnalysisStatus.PROCESSING)
        await db.execute(stmt)
        await db.commit()

    try:
        # Запускаем синхронный сбор в отдельном потоке
        total_height, viewport_height, screenshot_url, elements_data = await asyncio.to_thread(
            _collect_sync, analysis_id, page_id, url
        )

        # Ограничиваем количество элементов
        if len(elements_data) > settings.MAX_ELEMENTS_PER_PAGE:
            elements_data = elements_data[:settings.MAX_ELEMENTS_PER_PAGE]

        # Сохраняем элементы в Redis
        redis = await RedisClient.get_client()
        cache_key = f"analysis:{analysis_id}:elements"
        await redis.setex(cache_key, 3600, json.dumps(elements_data))

        # Обновляем запись страницы в БД
        async with async_session_maker() as db:
            stmt = update(Page).where(Page.id == page_id).values(
                page_height=total_height,
                viewport_height=viewport_height,
                screenshot_url=screenshot_url
            )
            await db.execute(stmt)
            await db.commit()

        # Запускаем модуль анализа
        from app.analyzer.engine import run_analysis
        async with async_session_maker() as db:
            await run_analysis(analysis_id, db)

    except Exception as e:
        async with async_session_maker() as db:
            stmt = update(Analysis).where(Analysis.id == analysis_id).values(
                status=AnalysisStatus.FAILED,
                completed_at=func.now()
            )
            await db.execute(stmt)
            await db.commit()
        print(f"Collector error for analysis {analysis_id}: {e}")
        raise