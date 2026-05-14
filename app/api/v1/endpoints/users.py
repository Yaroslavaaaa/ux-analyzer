from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token, PasswordChange
from app.services.user_service import UserService
from app.core.dependencies import get_current_user, get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/users", tags=["users"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Регистрация нового пользователя
    
    - **username**: уникальное имя пользователя (3-50 символов, буквы, цифры, _, -)
    - **email**: валидный email адрес
    - **password**: пароль (минимум 6 символов)
    """
    user_service = UserService(db)
    user = await user_service.create_user(user_data)
    return user

@router.post("/login", response_model=Token)
async def login_user(
    login_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Вход в систему, получение JWT токена
    """
    user_service = UserService(db)
    
    # Аутентификация
    user = await user_service.authenticate_user(
        login_data.username, 
        login_data.password
    )
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token = user_service.create_user_token(user)
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Получение информации о текущем авторизованном пользователе
    Требует наличия JWT токена в заголовке Authorization: Bearer <token>
    """
    return current_user

@router.get("/{username}", response_model=UserResponse)
async def get_user_by_username(
    username: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получение публичной информации о пользователе по username
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(username)
    return user



@router.post("/me/change-password")
async def change_password(
    password_data: PasswordChange,  # Изменяем на Pydantic модель
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Смена пароля текущего пользователя
    
    - **old_password**: текущий пароль
    - **new_password**: новый пароль (минимум 6 символов)
    """
    from app.core.security import verify_password, get_password_hash
    
    # Проверяем старый пароль
    if not verify_password(password_data.old_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Обновляем пароль
    current_user.password_hash = get_password_hash(password_data.new_password)
    await db.commit()
    
    return {"message": "Password changed successfully"}