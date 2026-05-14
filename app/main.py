import os
from fastapi import FastAPI, Depends, Header
from fastapi.staticfiles import StaticFiles
from app.api.v1.router import router as api_v1_router
from app.core.database import engine, Base
from app.core.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from contextlib import asynccontextmanager
from app.core.redis_client import RedisClient
from fastapi.middleware.cors import CORSMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    await RedisClient.get_client()  # инициализация
    yield
    await RedisClient.close()

app = FastAPI(
    title="UX Analyzer API",
    description="API for UX analysis of websites",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],  # или ["*"] для разработки, но безопаснее указать конкретный
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём папку для скриншотов, если её нет
os.makedirs("static/screenshots", exist_ok=True)

# Монтируем статические файлы (доступны по URL /static/...)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Подключаем роутеры
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "message": "UX Analyzer API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# ДИАГНОСТИЧЕСКИЙ ЭНДПОИНТ (оставляем как есть)
@app.get("/debug/check-auth")
async def debug_auth(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db)
):
    """Проверяет, как приходит заголовок авторизации"""
    
    result = {
        "received_header": authorization,
        "header_format": None,
        "token_valid": False,
        "user_found": False,
        "error": None
    }
    
    if not authorization:
        result["error"] = "No Authorization header"
        return result
    
    parts = authorization.split()
    if len(parts) != 2:
        result["error"] = f"Invalid format, got {len(parts)} parts"
        result["header_format"] = "invalid"
        return result
    
    scheme, token = parts
    result["header_format"] = f"Scheme: {scheme}, Token length: {len(token)}"
    
    if scheme.lower() != "bearer":
        result["error"] = f"Invalid scheme: {scheme}, expected Bearer"
        return result
    
    from app.core.security import decode_access_token
    payload = decode_access_token(token)
    
    if not payload:
        result["error"] = "Invalid token"
        return result
    
    result["token_valid"] = True
    username = payload.get("sub")
    result["username_from_token"] = username
    
    if username:
        user_result = await db.execute(
            select(User).where(User.username == username)
        )
        user = user_result.scalar_one_or_none()
        
        if user:
            result["user_found"] = True
            result["user_data"] = {
                "username": user.username,
                "email": user.email,
                "is_active": user.is_active
            }
        else:
            result["error"] = f"User '{username}' not found in database"
    
    return result