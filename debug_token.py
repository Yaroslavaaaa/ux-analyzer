import asyncio
from sqlalchemy import select
from app.core.database import async_session_maker
from app.models.user import User
from app.core.security import decode_access_token

async def debug_token():
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqb2huZG9lIiwiZXhwIjoxNzc2MjYxOTIzfQ.3etAITAeGcIFNyqGxzFpJ9Ak5OoAXG3vN95BNgwqqhM"
    
    print("1. Декодируем токен:")
    payload = decode_access_token(token)
    print(f"   Payload: {payload}")
    
    if payload:
        username = payload.get("sub")
        print(f"2. Username из токена: {username}")
        
        print("3. Ищем пользователя в БД:")
        async with async_session_maker() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if user:
                print(f"   ✅ Пользователь найден: {user.username}")
                print(f"   Email: {user.email}")
                print(f"   ID: {user.id}")
            else:
                print(f"   ❌ Пользователь '{username}' не найден в БД!")
                
                # Проверим всех пользователей
                result = await session.execute(select(User))
                all_users = result.scalars().all()
                print(f"\n   Все пользователи в БД:")
                for u in all_users:
                    print(f"   - {u.username}")
    else:
        print("❌ Не удалось декодировать токен")

if __name__ == "__main__":
    asyncio.run(debug_token())