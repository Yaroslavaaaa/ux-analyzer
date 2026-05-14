import asyncio
import sys
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent.parent.parent))

from app.core.database import async_session_maker
from app.core.metrics_loader import metrics_loader
from app.models.metric_definition import MetricDefinition
from sqlalchemy import select

async def sync_metrics():
    """Синхронизирует метрики из JSON файла с БД"""
    
    print("🔄 Starting metrics synchronization...")
    
    # Загружаем метрики из файла
    metrics, categories = metrics_loader.load_metrics(force_reload=True)
    
    async with async_session_maker() as db:
        # Получаем существующие метрики из БД
        existing = await db.execute(select(MetricDefinition))
        existing_metrics = {m.id: m for m in existing.scalars().all()}
        
        created = 0
        updated = 0
        
        for metric_data in metrics:
            metric_id = metric_data["id"]
            
            if metric_id in existing_metrics:
                # Обновляем существующую метрику
                metric = existing_metrics[metric_id]
                metric.name = metric_data.get("name", metric_id)
                metric.category = metric_data["category"]
                metric.type = metric_data["type"]
                metric.weight = metric_data.get("weight", 1.0)
                updated += 1
            else:
                # Создаем новую метрику
                metric = MetricDefinition(
                    id=metric_id,
                    name=metric_data.get("name", metric_id),
                    category=metric_data["category"],
                    type=metric_data["type"],
                    weight=metric_data.get("weight", 1.0)
                )
                db.add(metric)
                created += 1
        
        await db.commit()
        
        print(f"✅ Sync completed:")
        print(f"   - Created: {created} metrics")
        print(f"   - Updated: {updated} metrics")
        print(f"   - Total: {len(metrics)} metrics")
        
        # Выводим статистику по категориям
        print("\n📊 Metrics by category:")
        for category in categories:
            count = len([m for m in metrics if m["category"] == category])
            print(f"   - {category}: {count} metrics")

async def reset_metrics():
    """Сбрасывает все метрики в БД и пересоздает из файла"""
    
    print("⚠️  Resetting all metrics in database...")
    
    async with async_session_maker() as db:
        # Удаляем все существующие метрики
        await db.execute(MetricDefinition.__table__.delete())
        await db.commit()
        
        print("   All metrics deleted")
    
    # Создаем заново
    await sync_metrics()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        asyncio.run(reset_metrics())
    else:
        asyncio.run(sync_metrics())