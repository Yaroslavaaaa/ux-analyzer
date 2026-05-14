import asyncio
import sys
from pathlib import Path
from sqlalchemy import text

sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import engine, Base
from app.models import User, Project, MetricDefinition, Analysis, Page  # добавили Analysis и Page

async def init_db():
    print("🔨 Creating database tables...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully!")
    
    # Выводим список таблиц
    async with engine.connect() as conn:
        result = await conn.execute(
            text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
        )
        tables = result.fetchall()
        print("\n📋 Created tables:")
        for table in tables:
            print(f"   - {table[0]}")
    
    # Синхронизируем метрики
    print("\n🔄 Syncing metrics...")
    from app.scripts.sync_metrics import sync_metrics
    await sync_metrics()

if __name__ == "__main__":
    asyncio.run(init_db())